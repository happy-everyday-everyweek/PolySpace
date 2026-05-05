const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('polyspace', {
  config: {
    get: (key, defaultValue) => ipcRenderer.invoke('config:get', key, defaultValue),
    set: (key, value) => ipcRenderer.invoke('config:set', key, value)
  },
  screen: {
    click: (x, y) => ipcRenderer.invoke('screen:click', x, y),
    doubleClick: (x, y) => ipcRenderer.invoke('screen:doubleClick', x, y),
    rightClick: (x, y) => ipcRenderer.invoke('screen:rightClick', x, y),
    longPress: (x, y, duration) => ipcRenderer.invoke('screen:longPress', x, y, duration),
    type: (text) => ipcRenderer.invoke('screen:type', text),
    keyTap: (key) => ipcRenderer.invoke('screen:keyTap', key),
    keyCombo: (keys) => ipcRenderer.invoke('screen:keyCombo', keys),
    scroll: (amount) => ipcRenderer.invoke('screen:scroll', amount),
    scrollUp: (x, y, amount) => ipcRenderer.invoke('screen:scrollUp', x, y, amount),
    scrollDown: (x, y, amount) => ipcRenderer.invoke('screen:scrollDown', x, y, amount),
    moveMouse: (x, y) => ipcRenderer.invoke('screen:moveMouse', x, y),
    hover: (x, y, duration) => ipcRenderer.invoke('screen:hover', x, y, duration),
    drag: (startX, startY, endX, endY, duration) => ipcRenderer.invoke('screen:drag', startX, startY, endX, endY, duration),
    swipe: (startX, startY, endX, endY, duration) => ipcRenderer.invoke('screen:swipe', startX, startY, endX, endY, duration),
    getMousePos: () => ipcRenderer.invoke('screen:getMousePos'),
    screenshot: () => ipcRenderer.invoke('screen:screenshot'),
    getScreenSize: () => ipcRenderer.invoke('screen:getScreenSize'),
    wait: (ms) => ipcRenderer.invoke('screen:wait', ms),
    analyze: (instruction, options) => ipcRenderer.invoke('screen:analyze', instruction, options),
  },
  tools: {
    execute: (toolName, action, params) => ipcRenderer.invoke('tool:execute', toolName, action, params),
    list: () => ipcRenderer.invoke('tool:list'),
    capabilities: () => ipcRenderer.invoke('tool:capabilities'),
  },
  bridge: {
    status: () => ipcRenderer.invoke('bridge:status'),
    reconnect: () => ipcRenderer.invoke('bridge:reconnect'),
  },
  app: {
    reload: () => ipcRenderer.invoke('app:reload'),
    getFrontendUrl: () => ipcRenderer.invoke('app:getFrontendUrl')
  }
});
