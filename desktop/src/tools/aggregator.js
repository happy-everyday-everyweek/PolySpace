const { AutomationManagerExtended } = require('../automation/manager_extended');
const { DesktopFileManager } = require('./desktop_file_manager');
const { DesktopWindowManager } = require('./desktop_window_manager');
const { DesktopSystemManager } = require('./desktop_system_manager');
const { DesktopClipboardManager } = require('./desktop_clipboard_manager');
const { DesktopProcessManager } = require('./desktop_process_manager');

class DesktopToolAggregator {
  constructor() {
    this._tools = {
      screen_operation: new AutomationManagerExtended(),
      desktop_file: new DesktopFileManager(),
      desktop_window: new DesktopWindowManager(),
      desktop_system: new DesktopSystemManager(),
      desktop_clipboard: new DesktopClipboardManager(),
      desktop_process: new DesktopProcessManager(),
    };
  }

  getCapabilities() {
    const capabilities = [];
    for (const [name, tool] of Object.entries(this._tools)) {
      capabilities.push(...tool.getCapabilities());
    }
    return capabilities;
  }

  async executeAction(toolName, action, params = {}) {
    const tool = this._tools[toolName];
    if (!tool) {
      return { success: false, error: `Unknown tool: ${toolName}` };
    }
    try {
      return await tool.executeAction(action, params);
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  getToolNames() {
    return Object.keys(this._tools);
  }

  getTool(toolName) {
    return this._tools[toolName] || null;
  }

  get screenOperation() {
    return this._tools.screen_operation;
  }

  cleanup() {
    if (this._tools.screen_operation && this._tools.screen_operation.cleanup) {
      this._tools.screen_operation.cleanup();
    }
  }
}

module.exports = { DesktopToolAggregator };
