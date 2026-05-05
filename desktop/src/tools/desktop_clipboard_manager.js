class DesktopClipboardManager {
  constructor() {
    this._toolDefinition = {
      name: 'desktop_clipboard',
      description: 'Desktop clipboard operations - read, write, clear',
      actions: ['read', 'write', 'clear'],
    };
  }

  getCapabilities() {
    return [{
      name: this._toolDefinition.name,
      description: this._toolDefinition.description,
      actions: this._toolDefinition.actions,
      parameters: {
        action: { type: 'string', description: 'Action to perform' },
        text: { type: 'string', description: 'Text to write to clipboard' },
      },
    }];
  }

  async executeAction(action, params = {}) {
    switch (action) {
      case 'read':
        return this.read();
      case 'write':
        return this.write(params.text);
      case 'clear':
        return this.clear();
      default:
        throw new Error(`Unknown action: ${action}`);
    }
  }

  _runPowershell(script) {
    const { execSync } = require('child_process');
    try {
      return execSync('powershell -NoProfile -Command -', {
        input: script,
        encoding: 'utf-8',
        timeout: 5000,
        windowsHide: true,
      }).trim();
    } catch (e) {
      return null;
    }
  }

  _escapePS(str) {
    return String(str || '').replace(/'/g, "''");
  }

  read() {
    const result = this._runPowershell('Get-Clipboard');
    if (result === null) {
      return { success: false, error: 'Failed to read clipboard' };
    }
    return { success: true, text: result };
  }

  write(text) {
    if (text === undefined || text === null) {
      return { success: false, error: 'Missing text parameter' };
    }
    const escaped = this._escapePS(text);
    const result = this._runPowershell(`Set-Clipboard -Value '${escaped}'`);
    return { success: result !== null, text: String(text).substring(0, 100) };
  }

  clear() {
    const result = this._runPowershell('Set-Clipboard -Value ""');
    return { success: true };
  }
}

module.exports = { DesktopClipboardManager };
