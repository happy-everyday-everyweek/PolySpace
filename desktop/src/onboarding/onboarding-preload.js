const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('onboarding', {
  registerFileAssociations: (types) => ipcRenderer.invoke('onboarding:registerFileAssociations', types),
  unregisterFileAssociations: (types) => ipcRenderer.invoke('onboarding:unregisterFileAssociations', types),
  getFileAssociations: () => ipcRenderer.invoke('onboarding:getFileAssociations'),
  complete: () => ipcRenderer.invoke('onboarding:complete'),
  getConfig: (key, defaultValue) => ipcRenderer.invoke('config:get', key, defaultValue),
  setConfig: (key, value) => ipcRenderer.invoke('config:set', key, value),
  openExternal: (url) => ipcRenderer.invoke('onboarding:openExternal', url),
});
