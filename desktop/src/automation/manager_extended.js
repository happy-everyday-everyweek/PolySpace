const { AutomationManager } = require('./manager');

class AutomationManagerExtended extends AutomationManager {
  constructor() {
    super();
    this._toolDefinition = {
      name: 'screen_operation',
      description: 'Screen operation tool - multimodal AI analysis and click/swipe/input/key operations',
      actions: [
        'click', 'double_click', 'right_click', 'long_press', 'swipe',
        'drag', 'hover', 'input_text', 'key_tap', 'key_combo',
        'scroll_up', 'scroll_down', 'scroll',
        'move_mouse', 'get_mouse_pos', 'get_screen_size',
        'screenshot', 'analyze', 'wait'
      ]
    };
  }

  getCapabilities() {
    return [{
      name: this._toolDefinition.name,
      description: this._toolDefinition.description,
      actions: this._toolDefinition.actions,
      parameters: {
        action: { type: 'string', description: 'Action to perform' },
        x: { type: 'integer', description: 'X coordinate' },
        y: { type: 'integer', description: 'Y coordinate' },
        start_x: { type: 'integer', description: 'Swipe/Drag start X' },
        start_y: { type: 'integer', description: 'Swipe/Drag start Y' },
        end_x: { type: 'integer', description: 'Swipe/Drag end X' },
        end_y: { type: 'integer', description: 'Swipe/Drag end Y' },
        duration: { type: 'integer', description: 'Duration in ms' },
        text: { type: 'string', description: 'Text to input' },
        key: { type: 'string', description: 'Key or key combination' },
        keys: { type: 'array', items: { type: 'string' }, description: 'Key combination array' },
        amount: { type: 'integer', description: 'Scroll amount' },
        button: { type: 'string', enum: ['left', 'right', 'middle'], description: 'Mouse button' },
        instruction: { type: 'string', description: 'Natural language instruction for AI analysis' },
        wait_ms: { type: 'integer', description: 'Wait duration in milliseconds' },
      }
    }];
  }

  async executeAction(action, params = {}) {
    switch (action) {
      case 'click':
        return this.click(params.x, params.y);
      case 'double_click':
        return this.doubleClick(params.x, params.y);
      case 'right_click':
        return this.rightClick(params.x, params.y);
      case 'long_press':
        return this.longPress(params.x, params.y, params.duration);
      case 'swipe':
        return this.swipe(params.start_x, params.start_y, params.end_x, params.end_y, params.duration);
      case 'drag':
        return this.drag(params.start_x, params.start_y, params.end_x, params.end_y, params.duration);
      case 'hover':
        return this.hover(params.x, params.y, params.duration);
      case 'input_text':
        return this.typeText(params.text);
      case 'key_tap':
        return this.keyTap(params.key);
      case 'key_combo':
        return this.keyCombo(params.keys);
      case 'scroll':
        return this.scroll(params.amount);
      case 'scroll_up':
        return this.scrollUp(params.x, params.y, params.amount);
      case 'scroll_down':
        return this.scrollDown(params.x, params.y, params.amount);
      case 'move_mouse':
        return this.moveMouse(params.x, params.y);
      case 'get_mouse_pos':
        return this.getMousePos();
      case 'get_screen_size':
        return this.getScreenSize();
      case 'screenshot':
        return this.takeScreenshot();
      case 'wait':
        return this.wait(params.wait_ms || 500);
      case 'analyze':
        return this._analyzeWithScreenshot(params);
      default:
        throw new Error(`Unknown action: ${action}`);
    }
  }

  async _analyzeWithScreenshot(params) {
    const instruction = params.instruction || '';
    if (!instruction) {
      return { success: false, error: 'Missing instruction for analyze' };
    }

    const screenshotBase64 = await this.takeScreenshot();
    if (!screenshotBase64) {
      return { success: false, error: 'Failed to take screenshot' };
    }

    const screenSize = this.getScreenSize();

    const host = params.host || 'localhost';
    const port = params.port || 8000;

    try {
      const http = require('http');
      const payload = JSON.stringify({
        instruction,
        screenshot: screenshotBase64,
        screenshot_format: 'png',
        has_multimodal_input: true,
        platform: 'desktop',
        screen_width: screenSize.width,
        screen_height: screenSize.height,
      });

      const result = await new Promise((resolve, reject) => {
        const req = http.request({
          hostname: host,
          port: port,
          path: '/api/v1/models/autoglm',
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(payload),
          },
          timeout: 120000,
        }, (res) => {
          let body = '';
          res.on('data', chunk => body += chunk);
          res.on('end', () => {
            try {
              resolve(JSON.parse(body));
            } catch (e) {
              reject(new Error(`Parse error: ${e.message}`));
            }
          });
        });

        req.on('error', reject);
        req.on('timeout', () => { req.destroy(); reject(new Error('Request timeout')); });
        req.write(payload);
        req.end();
      });

      const actions = result.actions || [];
      const executedResults = [];

      for (const act of actions) {
        try {
          const execResult = await this.executeAction(act.type, act.params || {});
          executedResults.push({ type: act.type, success: !!execResult, result: execResult });
          await this.wait(300);
        } catch (e) {
          executedResults.push({ type: act.type, success: false, error: e.message });
          break;
        }
      }

      return {
        success: true,
        action_count: actions.length,
        executed: executedResults,
      };
    } catch (e) {
      return { success: false, error: `Analyze failed: ${e.message}` };
    }
  }
}

module.exports = { AutomationManagerExtended };
