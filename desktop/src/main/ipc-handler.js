const { ipcMain } = require('electron');

const ErrorCode = {
  UNAUTHORIZED: 'UNAUTHORIZED',
  NOT_FOUND: 'NOT_FOUND',
  INVALID_PARAMS: 'INVALID_PARAMS',
  INTERNAL_ERROR: 'INTERNAL_ERROR',
  TOOL_NOT_AVAILABLE: 'TOOL_NOT_AVAILABLE',
};

const ValidationStrategy = {
  BASIC: 'basic',
  STRICT: 'strict',
  NONE: 'none',
};

function _validateSender(event) {
  if (!event.senderFrame) return false;
  const url = event.senderFrame.url;
  try {
    const parsed = new URL(url);
    if (parsed.hostname === 'localhost' || parsed.hostname === '127.0.0.1') return true;
    if (url.endsWith('onboarding.html')) return true;
  } catch (_) {}
  return false;
}

const validators = {
  [ValidationStrategy.BASIC]: (event) => _validateSender(event),
  [ValidationStrategy.STRICT]: (event) => _validateSender(event),
  [ValidationStrategy.NONE]: () => true,
};

function wrapIpcHandler(handler, options = {}) {
  const {
    defaultValue = null,
    validationStrategy = ValidationStrategy.BASIC,
    logPrefix = 'IPC',
    log,
    errorResponseBuilder = null,
  } = options;

  const validator = validators[validationStrategy] || validators[ValidationStrategy.BASIC];

  return async (event, ...params) => {
    if (!validator(event)) {
      if (log) log.warn(`${logPrefix}: Unauthorized access attempt`);
      return defaultValue;
    }

    try {
      const result = await handler(event, ...params);
      return result;
    } catch (err) {
      if (log) log.error(`${logPrefix} failed:`, err.message);
      if (errorResponseBuilder) {
        return errorResponseBuilder(err);
      }
      return defaultValue;
    }
  };
}

const dynamicError = (err) => ({ success: false, error: err.message });

function registerIpcHandlers(ctx) {
  const {
    log,
    configStore,
    toolAggregator,
    screenRecorder,
    mainWindow,
    onboardingWindow,
    deviceBridge,
    shell,
    getFrontendUrl,
    setupDeviceBridge,
    getFileAssociations,
    registerFileAssociations,
    unregisterFileAssociations,
  } = ctx;

  const screenOp = (action, paramsBuilder, fallback = false) => ({
    handler: (event, ...args) => {
      const params = paramsBuilder(...args);
      return toolAggregator?.executeAction('screen_operation', action, params) ?? fallback;
    },
    options: { defaultValue: fallback, log },
  });

  const handlers = {
    'config:get': {
      handler: (event, key, defaultValue) => configStore.get(key, defaultValue),
      options: { defaultValue: undefined, log },
    },
    'config:set': {
      handler: (event, key, value) => { configStore.set(key, value); return true; },
      options: { defaultValue: false, log },
    },

    'screen:click': screenOp('click', (x, y) => ({ x, y })),
    'screen:doubleClick': screenOp('double_click', (x, y) => ({ x, y })),
    'screen:rightClick': screenOp('right_click', (x, y) => ({ x, y })),
    'screen:longPress': screenOp('long_press', (x, y, duration) => ({ x, y, duration })),
    'screen:type': screenOp('input_text', (text) => ({ text })),
    'screen:keyTap': screenOp('key_tap', (key) => ({ key })),
    'screen:keyCombo': screenOp('key_combo', (keys) => ({ keys })),
    'screen:scroll': screenOp('scroll', (amount) => ({ amount })),
    'screen:scrollUp': screenOp('scroll_up', (x, y, amount) => ({ x, y, amount })),
    'screen:scrollDown': screenOp('scroll_down', (x, y, amount) => ({ x, y, amount })),
    'screen:moveMouse': screenOp('move_mouse', (x, y) => ({ x, y })),
    'screen:hover': screenOp('hover', (x, y, duration) => ({ x, y, duration })),
    'screen:drag': screenOp('drag', (startX, startY, endX, endY, duration) => ({
      start_x: startX, start_y: startY, end_x: endX, end_y: endY, duration,
    })),
    'screen:swipe': screenOp('swipe', (startX, startY, endX, endY, duration) => ({
      start_x: startX, start_y: startY, end_x: endX, end_y: endY, duration,
    })),
    'screen:getMousePos': {
      handler: () => toolAggregator?.executeAction('screen_operation', 'get_mouse_pos', {}) ?? { x: 0, y: 0 },
      options: { defaultValue: { x: 0, y: 0 }, log },
    },
    'screen:screenshot': {
      handler: () => toolAggregator?.executeAction('screen_operation', 'screenshot', {}) ?? null,
      options: { defaultValue: null, log },
    },
    'screen:getScreenSize': {
      handler: () => toolAggregator?.executeAction('screen_operation', 'get_screen_size', {}) ?? { width: 0, height: 0 },
      options: { defaultValue: { width: 0, height: 0 }, log },
    },
    'screen:wait': screenOp('wait', (ms) => ({ wait_ms: ms })),

    'screen:analyze': {
      handler: async (event, instruction, options) => {
        if (toolAggregator) {
          return await toolAggregator.executeAction('screen_operation', 'analyze', {
            instruction,
            host: options?.host || configStore.get('backend.host', 'localhost'),
            port: options?.port || configStore.get('backend.port', 8000),
          });
        }
        return { success: false, error: 'Tool aggregator not initialized' };
      },
      options: { defaultValue: { success: false, error: 'Unauthorized' }, errorResponseBuilder: dynamicError, log },
    },

    'recorder:start': {
      handler: async (event, options) => {
        if (screenRecorder) {
          return await screenRecorder.startRecording(options || {});
        }
        return { success: false, error: 'Screen recorder not available' };
      },
      options: { defaultValue: { success: false, error: 'Unauthorized' }, errorResponseBuilder: dynamicError, log },
    },
    'recorder:stop': {
      handler: async () => screenRecorder ? await screenRecorder.stopRecording() : null,
      options: { defaultValue: null, log },
    },

    'tool:execute': {
      handler: async (event, toolName, action, params) => {
        if (toolAggregator) {
          return await toolAggregator.executeAction(toolName, action, params || {});
        }
        return { success: false, error: 'Tool aggregator not initialized' };
      },
      options: { defaultValue: { success: false, error: 'Unauthorized' }, errorResponseBuilder: dynamicError, log },
    },
    'tool:list': {
      handler: () => toolAggregator ? toolAggregator.getToolNames() : [],
      options: { defaultValue: [], log },
    },
    'tool:capabilities': {
      handler: () => toolAggregator ? toolAggregator.getCapabilities() : [],
      options: { defaultValue: [], log },
    },

    'app:reload': {
      handler: () => { mainWindow?.reload(); return true; },
      options: { defaultValue: false, log },
    },
    'app:getFrontendUrl': {
      handler: () => getFrontendUrl(),
      options: { defaultValue: '', log },
    },

    'bridge:status': {
      handler: () => ({
        connected: deviceBridge?.connected ?? false,
        deviceId: deviceBridge?.deviceId ?? '',
      }),
      options: { defaultValue: { connected: false, deviceId: '' }, log },
    },
    'bridge:reconnect': {
      handler: () => {
        if (deviceBridge) {
          deviceBridge.disconnect();
        }
        setupDeviceBridge();
        return true;
      },
      options: { defaultValue: false, log },
    },

    'onboarding:registerFileAssociations': {
      handler: async (event, types) => await registerFileAssociations(types),
      options: { defaultValue: { success: false, error: 'Unauthorized' }, errorResponseBuilder: dynamicError, log },
    },
    'onboarding:unregisterFileAssociations': {
      handler: async (event, types) => await unregisterFileAssociations(types),
      options: { defaultValue: { success: false, error: 'Unauthorized' }, errorResponseBuilder: dynamicError, log },
    },
    'onboarding:getFileAssociations': {
      handler: () => getFileAssociations(),
      options: { defaultValue: {}, log },
    },
    'onboarding:complete': {
      handler: () => {
        configStore.set('onboarding.completed', true);
        if (onboardingWindow) {
          onboardingWindow.close();
        }
        return true;
      },
      options: { defaultValue: false, log },
    },
    'onboarding:openExternal': {
      handler: (event, url) => {
        try {
          const parsed = new URL(url);
          if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
            return false;
          }
        } catch (_) {
          return false;
        }
        shell.openExternal(url);
        return true;
      },
      options: { defaultValue: false, log },
    },
  };

  for (const [channel, config] of Object.entries(handlers)) {
    ipcMain.handle(channel, wrapIpcHandler(config.handler, {
      ...config.options,
      logPrefix: channel,
    }));
  }
}

module.exports = { registerIpcHandlers, wrapIpcHandler, ErrorCode, ValidationStrategy };
