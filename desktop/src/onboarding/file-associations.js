const { exec } = require('child_process');
const path = require('path');
const log = console;

const FILE_ASSOCIATIONS = {
  ppt: { extensions: ['.ppt', '.pptx'], name: 'PowerPoint Presentation', mimeType: 'application/vnd.ms-powerpoint' },
  excel: { extensions: ['.xls', '.xlsx'], name: 'Excel Spreadsheet', mimeType: 'application/vnd.ms-excel' },
  word: { extensions: ['.doc', '.docx'], name: 'Word Document', mimeType: 'application/msword' },
  pdf: { extensions: ['.pdf'], name: 'PDF Document', mimeType: 'application/pdf' },
};

function getExePath() {
  if (process.platform === 'win32') {
    const exePath = process.execPath;
    if (exePath.toLowerCase().includes('electron')) {
      return path.join(__dirname, '../../dist/win-unpacked/PolySpace.exe');
    }
    return exePath;
  }
  return process.execPath;
}

function registerFileAssociations(selectedTypes) {
  if (process.platform !== 'win32') {
    log.warn('File association registration is only supported on Windows');
    return Promise.resolve({ success: false, error: 'Not supported on this platform' });
  }

  const exePath = getExePath();
  const promises = [];

  for (const typeKey of selectedTypes) {
    const assoc = FILE_ASSOCIATIONS[typeKey];
    if (!assoc) continue;

    for (const ext of assoc.extensions) {
      promises.push(registerSingleAssociation(ext, assoc.name, exePath));
    }
  }

  return Promise.allSettled(promises).then(results => {
    const succeeded = results.filter(r => r.status === 'fulfilled' && r.value.success).length;
    const total = promises.length;
    return {
      success: succeeded > 0,
      message: `Registered ${succeeded}/${total} file associations`,
    };
  });
}

function registerSingleAssociation(extension, typeName, exePath) {
  const progId = `PolySpace${extension.replace('.', '').toUpperCase()}`;
  const escapedExePath = `"${exePath}"`;
  const commandValue = `${escapedExePath} "%1"`;

  const commands = [
    `reg add "HKCU\\Software\\Classes\\${progId}" /ve /d "${typeName} (PolySpace)" /f`,
    `reg add "HKCU\\Software\\Classes\\${progId}\\shell\\open\\command" /ve /d "${commandValue.replace(/"/g, '\\"')}" /f`,
    `reg add "HKCU\\Software\\Classes\\${progId}\\DefaultIcon" /ve /d "${escapedExePath.replace(/"/g, '\\"')},0" /f`,
    `reg add "HKCU\\Software\\Classes\\${extension}" /ve /d "${progId}" /f`,
  ];

  const commandChain = commands.join(' && ');

  return new Promise((resolve) => {
    exec(commandChain, (error, stdout, stderr) => {
      if (error) {
        log.error(`Failed to register ${extension}:`, error.message);
        resolve({ success: false, extension, error: error.message });
      } else {
        log.info(`Registered ${extension} -> ${progId}`);
        resolve({ success: true, extension });
      }
    });
  });
}

function unregisterFileAssociations(selectedTypes) {
  if (process.platform !== 'win32') {
    return Promise.resolve({ success: false, error: 'Not supported on this platform' });
  }

  const promises = [];

  for (const typeKey of selectedTypes) {
    const assoc = FILE_ASSOCIATIONS[typeKey];
    if (!assoc) continue;

    for (const ext of assoc.extensions) {
      const progId = `PolySpace${ext.replace('.', '').toUpperCase()}`;
      promises.push(unregisterSingleAssociation(ext, progId));
    }
  }

  return Promise.allSettled(promises).then(results => {
    const succeeded = results.filter(r => r.status === 'fulfilled' && r.value.success).length;
    const total = promises.length;
    return {
      success: succeeded > 0,
      message: `Unregistered ${succeeded}/${total} file associations`,
    };
  });
}

function unregisterSingleAssociation(extension, progId) {
  const commands = [
    `reg delete "HKCU\\Software\\Classes\\${progId}" /f`,
    `reg delete "HKCU\\Software\\Classes\\${extension}" /ve /f`,
  ];

  const commandChain = commands.join(' && ');

  return new Promise((resolve) => {
    exec(commandChain, (error) => {
      if (error) {
        resolve({ success: false, extension, error: error.message });
      } else {
        resolve({ success: true, extension });
      }
    });
  });
}

function getFileAssociations() {
  return FILE_ASSOCIATIONS;
}

module.exports = {
  registerFileAssociations,
  unregisterFileAssociations,
  getFileAssociations,
};
