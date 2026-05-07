const { app, BrowserWindow, Menu, Tray, session, dialog, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const http = require('http');
const Store = require('electron-store');
const { DesktopToolAggregator } = require('../tools/aggregator');
const { DeviceBridgeClient } = require('../bridge/device_bridge_client');
const { ScreenRecorderManager } = require('../automation/screen_recorder');
const { registerFileAssociations, unregisterFileAssociations, getFileAssociations } = require('../onboarding/file-associations');
const { registerIpcHandlers } = require('./ipc-handler');

let log = console;
try {
  const electronLog = require('electron-log');
  electronLog.transports.file.resolvePathFn = () => path.join(app.getPath('userData'), 'logs', 'main.log');
  electronLog.transports.file.maxSize = 5 * 1024 * 1024;
  log = electronLog.scope('main');
} catch (_) {}

let mainWindow = null;
let onboardingWindow = null;
let tray = null;
let toolAggregator = null;
let deviceBridge = null;
let screenRecorder = null;
let backendProcess = null;

const isDev = process.argv.includes('--dev');

const configStore = new Store({ name: 'polyspace-config' });

const BACKEND_PORT = 8000;
const BACKEND_HOST = '127.0.0.1';

function startBackend() {
  return new Promise((resolve, reject) => {
    const backendDir = isDev
      ? path.join(__dirname, '..', '..', '..', 'backend')
      : path.join(process.resourcesPath, 'backend');

    if (!fs.existsSync(path.join(backendDir, 'app', 'main.py'))) {
      log.error('Backend not found at:', backendDir);
      reject(new Error('Backend directory not found'));
      return;
    }

    const dataDir = path.join(app.getPath('userData'), 'data');
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true });
    }

    let uvPath = 'uv';
    if (!isDev) {
      const bundledUv = path.join(process.resourcesPath, 'uv', 'uv.exe');
      if (fs.existsSync(bundledUv)) {
        uvPath = bundledUv;
      }
    }

    const frontendDistDir = isDev
      ? path.join(__dirname, '..', '..', '..', 'frontend', 'dist')
      : path.join(process.resourcesPath, 'frontend-dist');

    backendProcess = spawn(uvPath, ['run', 'uvicorn', 'app.main:app', '--host', BACKEND_HOST, '--port', String(BACKEND_PORT)], {
      cwd: backendDir,
      env: {
        ...process.env,
        POLYSPACE_PORT: String(BACKEND_PORT),
        POLYSPACE_DATA_DIR: dataDir,
        POLYSPACE_FRONTEND_DIR: frontendDistDir,
      },
      stdio: ['ignore', 'pipe', 'pipe'],
      windowsHide: true,
    });

    backendProcess.stdout.on('data', (data) => {
      const msg = data.toString().trim();
      log.info('[backend]', msg);
      if (msg.includes('Uvicorn running on')) {
        resolve();
      }
    });

    backendProcess.stderr.on('data', (data) => {
      log.error('[backend]', data.toString().trim());
    });

    backendProcess.on('error', (err) => {
      log.error('[backend] Failed to start:', err.message);
      reject(err);
    });

    backendProcess.on('exit', (code) => {
      log.info('[backend] Exited with code:', code);
    });

    const maxWait = 30000;
    const startTime = Date.now();
    const checkInterval = setInterval(() => {
      if (Date.now() - startTime > maxWait) {
        clearInterval(checkInterval);
        reject(new Error('Backend startup timeout'));
        return;
      }
      http.get(`http://${BACKEND_HOST}:${BACKEND_PORT}/health`, (res) => {
        if (res.statusCode === 200) {
          clearInterval(checkInterval);
          resolve();
        }
      }).on('error', () => {});
    }, 1000);
  });
}

function stopBackend() {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
    log.info('Backend stopped');
  }
}

function createOnboardingWindow() {
  onboardingWindow = new BrowserWindow({
    width: 640,
    height: 520,
    minWidth: 580,
    minHeight: 480,
    title: 'PolySpace Setup',
    icon: path.join(__dirname, '../../resources/icon.png'),
    webPreferences: {
      preload: path.join(__dirname, '../onboarding/onboarding-preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
    frame: true,
    resizable: true,
    show: false,
    autoHideMenuBar: true,
  });

  onboardingWindow.loadFile(path.join(__dirname, '../onboarding/onboarding.html'));

  onboardingWindow.once('ready-to-show', () => {
    onboardingWindow.show();
  });

  onboardingWindow.on('closed', () => {
    onboardingWindow = null;
    if (!configStore.get('onboarding.completed', false)) {
      configStore.set('onboarding.completed', true);
    }
    if (!mainWindow) {
      createWindow();
      createTray();
      setupDeviceBridge();
    }
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 768,
    title: 'PolySpace',
    icon: path.join(__dirname, '../../resources/icon.png'),
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
    frame: true,
    show: false,
  });

  if (!isDev) {
    session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
      callback({
        responseHeaders: {
          ...details.responseHeaders,
          'Content-Security-Policy': [
            "default-src 'self'; " +
            "script-src 'self'; " +
            "style-src 'self' 'unsafe-inline'; " +
            "connect-src 'self' ws://localhost:* http://localhost:*; " +
            "img-src 'self' data:; " +
            "font-src 'self';",
          ],
        },
      });
    });
  }

  const frontendUrl = getFrontendUrl();
  mainWindow.loadURL(frontendUrl);

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  if (isDev) {
    mainWindow.webContents.openDevTools();
  }
}

function getFrontendUrl() {
  const host = configStore.get('backend.host', 'localhost');
  const port = configStore.get('backend.port', 8000);
  return `http://${host}:${port}`;
}

function getBackendWsUrl() {
  const host = configStore.get('backend.host', 'localhost');
  const port = configStore.get('backend.port', 8000);
  return `ws://${host}:${port}`;
}

function createTray() {
  try {
    tray = new Tray(path.join(__dirname, '../../resources/icon.png'));
    const contextMenu = Menu.buildFromTemplate([
      { label: 'Show PolySpace', click: () => mainWindow?.show() },
      { label: 'Quit', click: () => app.quit() },
    ]);
    tray.setToolTip('PolySpace');
    tray.setContextMenu(contextMenu);
  } catch (err) {
    log.error('Failed to create tray:', err.message);
  }
}

function setupDeviceBridge() {
  try {
    const wsUrl = getBackendWsUrl();
    const capabilities = toolAggregator ? toolAggregator.getCapabilities() : [];
    deviceBridge = new DeviceBridgeClient(wsUrl, '', 'PolySpace-Desktop', 'windows', capabilities);
    deviceBridge.setToolExecutor(async (tool, action, params) => {
      if (toolAggregator) {
        return await toolAggregator.executeAction(tool, action, params);
      }
      return { error: 'Tool aggregator not initialized' };
    });
    deviceBridge.connect();
  } catch (err) {
    log.error('Failed to setup device bridge:', err.message);
  }
}

function setupIPC() {
  registerIpcHandlers({
    log,
    configStore,
    toolAggregator,
    screenRecorder,
    get mainWindow() { return mainWindow; },
    get onboardingWindow() { return onboardingWindow; },
    deviceBridge,
    shell,
    getFrontendUrl,
    setupDeviceBridge,
    getFileAssociations,
    registerFileAssociations,
    unregisterFileAssociations,
  });
}

app.whenReady().then(async () => {
  toolAggregator = new DesktopToolAggregator();
  try {
    screenRecorder = new ScreenRecorderManager();
  } catch (err) {
    log.error('Failed to initialize screen recorder:', err.message);
  }
  setupIPC();

  if (!isDev) {
    try {
      log.info('Starting bundled backend...');
      await startBackend();
      log.info('Backend started successfully');
    } catch (err) {
      log.error('Failed to start backend:', err.message);
      dialog.showErrorBox('Backend Error', 'Failed to start backend service: ' + err.message);
    }
  }

  const onboardingCompleted = configStore.get('onboarding.completed', false);
  if (!onboardingCompleted) {
    createOnboardingWindow();
  } else {
    createWindow();
    createTray();
    setupDeviceBridge();
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  if (deviceBridge) {
    deviceBridge.disconnect();
  }
  toolAggregator?.cleanup();
  stopBackend();
});

process.on('uncaughtException', (err) => {
  log.error('Uncaught exception:', err);
  if (mainWindow) {
    dialog.showErrorBox('PolySpace - Unexpected Error', err.message);
  }
});

process.on('unhandledRejection', (reason) => {
  log.error('Unhandled rejection:', reason);
});
