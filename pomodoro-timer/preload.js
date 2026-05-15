const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("pomodoro", {
  setAlwaysOnTop: (flag) => ipcRenderer.invoke("set-always-on-top", flag),
});
