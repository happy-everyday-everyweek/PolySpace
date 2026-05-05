let robot = null;
let screenshot = null;

try {
  robot = require('robotjs');
} catch (e) {
  console.warn('robotjs not available, desktop automation disabled');
}

try {
  screenshot = require('screenshot-desktop');
} catch (e) {
  console.warn('screenshot-desktop not available, screenshot disabled');
}

class AutomationManager {
  constructor() {
    this._available = robot !== null;
  }

  get available() {
    return this._available;
  }

  click(x, y) {
    if (!this._available) return false;
    try {
      robot.moveMouse(x, y);
      robot.mouseClick();
      return true;
    } catch (e) {
      return false;
    }
  }

  doubleClick(x, y) {
    if (!this._available) return false;
    try {
      robot.moveMouse(x, y);
      robot.mouseClick('left', true);
      return true;
    } catch (e) {
      return false;
    }
  }

  rightClick(x, y) {
    if (!this._available) return false;
    try {
      robot.moveMouse(x, y);
      robot.mouseClick('right');
      return true;
    } catch (e) {
      return false;
    }
  }

  async longPress(x, y, duration = 500) {
    if (!this._available) return false;
    try {
      robot.moveMouse(x, y);
      robot.mouseToggle('down');
      await this._sleep(duration);
      robot.mouseToggle('up');
      return true;
    } catch (e) {
      return false;
    }
  }

  typeText(text) {
    if (!this._available) return false;
    try {
      robot.typeString(text);
      return true;
    } catch (e) {
      return false;
    }
  }

  keyTap(key) {
    if (!this._available) return false;
    try {
      robot.keyTap(key);
      return true;
    } catch (e) {
      return false;
    }
  }

  keyCombo(keys) {
    if (!this._available) return false;
    try {
      robot.keyTap(keys[keys.length - 1], keys.slice(0, -1));
      return true;
    } catch (e) {
      return false;
    }
  }

  scroll(amount) {
    if (!this._available) return false;
    try {
      robot.scrollMouse(0, amount);
      return true;
    } catch (e) {
      return false;
    }
  }

  scrollUp(x, y, amount = 5) {
    if (!this._available) return false;
    try {
      if (x !== undefined && y !== undefined) {
        robot.moveMouse(x, y);
      }
      robot.scrollMouse(0, amount);
      return true;
    } catch (e) {
      return false;
    }
  }

  scrollDown(x, y, amount = 5) {
    if (!this._available) return false;
    try {
      if (x !== undefined && y !== undefined) {
        robot.moveMouse(x, y);
      }
      robot.scrollMouse(0, -amount);
      return true;
    } catch (e) {
      return false;
    }
  }

  moveMouse(x, y) {
    if (!this._available) return false;
    try {
      robot.moveMouse(x, y);
      return true;
    } catch (e) {
      return false;
    }
  }

  async hover(x, y, duration = 300) {
    if (!this._available) return false;
    try {
      robot.moveMouse(x, y);
      await this._sleep(duration);
      return true;
    } catch (e) {
      return false;
    }
  }

  async drag(startX, startY, endX, endY, duration = 300) {
    if (!this._available) return false;
    try {
      robot.moveMouse(startX, startY);
      robot.mouseToggle('down');
      const steps = Math.max(10, Math.ceil(duration / 16));
      const dx = (endX - startX) / steps;
      const dy = (endY - startY) / steps;
      for (let i = 1; i <= steps; i++) {
        robot.moveMouse(Math.round(startX + dx * i), Math.round(startY + dy * i));
        await this._sleep(Math.floor(duration / steps));
      }
      robot.mouseToggle('up');
      return true;
    } catch (e) {
      try { robot.mouseToggle('up'); } catch (_) {}
      return false;
    }
  }

  async swipe(startX, startY, endX, endY, duration = 300) {
    return this.drag(startX, startY, endX, endY, duration);
  }

  getMousePos() {
    if (!this._available) return { x: 0, y: 0 };
    try {
      return robot.getMousePos();
    } catch (e) {
      return { x: 0, y: 0 };
    }
  }

  getScreenSize() {
    if (!this._available) return { width: 0, height: 0 };
    try {
      return robot.getScreenSize();
    } catch (e) {
      return { width: 0, height: 0 };
    }
  }

  async takeScreenshot() {
    if (!screenshot) return null;
    try {
      const imgBuffer = await screenshot({ format: 'png' });
      return imgBuffer.toString('base64');
    } catch (e) {
      return null;
    }
  }

  async wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async _sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  cleanup() {
    this._available = false;
  }
}

module.exports = { AutomationManager };
