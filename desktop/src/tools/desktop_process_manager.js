const { execSync, spawn } = require('child_process');
const os = require('os');

class DesktopProcessManager {
  constructor() {
    this._toolDefinition = {
      name: 'desktop_process',
      description: 'Desktop process management - list, kill, spawn, monitor',
      actions: ['list', 'kill', 'spawn', 'get_info', 'monitor'],
    };
  }

  getCapabilities() {
    return [{
      name: this._toolDefinition.name,
      description: this._toolDefinition.description,
      actions: this._toolDefinition.actions,
      parameters: {
        action: { type: 'string', description: 'Action to perform' },
        pid: { type: 'integer', description: 'Process ID' },
        name: { type: 'string', description: 'Process name' },
        command: { type: 'string', description: 'Command to spawn' },
        args: { type: 'array', items: { type: 'string' }, description: 'Command arguments' },
        signal: { type: 'string', description: 'Signal to send' },
      },
    }];
  }

  async executeAction(action, params = {}) {
    switch (action) {
      case 'list':
        return this.listProcesses(params.name);
      case 'kill':
        return this.killProcess(params.pid, params.name, params.signal);
      case 'spawn':
        return this.spawnProcess(params.command, params.args);
      case 'get_info':
        return this.getProcessInfo(params.pid, params.name);
      case 'monitor':
        return this.monitorProcesses();
      default:
        throw new Error(`Unknown action: ${action}`);
    }
  }

  _escapePS(str) {
    return String(str || '').replace(/'/g, "''");
  }

  _escapePSFilter(str) {
    return String(str || '').replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  listProcesses(nameFilter) {
    try {
      const cmd = nameFilter
        ? `powershell -NoProfile -Command -`
        : `powershell -NoProfile -Command -`;
      const script = nameFilter
        ? `Get-Process -Name '*${this._escapePSFilter(nameFilter)}*' -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,CPU,WorkingSet64,StartTime | ConvertTo-Json -Compress`
        : `Get-Process | Where-Object {$_.MainWindowTitle -ne '' -or $_.WorkingSet64 -gt 10MB} | Select-Object Id,ProcessName,CPU,WorkingSet64,StartTime | ConvertTo-Json -Compress`;
      const output = execSync(cmd, {
        input: script,
        encoding: 'utf-8',
        timeout: 10000,
        windowsHide: true,
      }).trim();
      if (!output) return { success: true, processes: [], count: 0 };
      const data = JSON.parse(output);
      const processes = (Array.isArray(data) ? data : [data]).map(p => ({
        pid: p.Id,
        name: p.ProcessName,
        cpu_percent: p.CPU ? Math.round(p.CPU * 100) / 100 : 0,
        memory_bytes: p.WorkingSet64 || 0,
        memory_mb: Math.round((p.WorkingSet64 || 0) / 1048576 * 100) / 100,
        start_time: p.StartTime || null,
      }));
      return { success: true, processes, count: processes.length };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  killProcess(pid, name, signal) {
    try {
      if (pid) {
        const numPid = Number(pid);
        if (!Number.isFinite(numPid) || numPid <= 0) {
          return { success: false, error: 'Invalid pid' };
        }
        process.kill(numPid, signal || 'SIGTERM');
        return { success: true, pid: numPid, signal: signal || 'SIGTERM' };
      }
      if (name) {
        const safeName = String(name).replace(/[^a-zA-Z0-9_.\- ]/g, '');
        if (!safeName) {
          return { success: false, error: 'Invalid process name' };
        }
        const script = `Stop-Process -Name '${this._escapePS(safeName)}' -Force -ErrorAction SilentlyContinue; (Get-Process -Name '${this._escapePS(safeName)}' -ErrorAction SilentlyContinue).Count`;
        const output = execSync('powershell -NoProfile -Command -', {
          input: script,
          encoding: 'utf-8',
          timeout: 5000,
          windowsHide: true,
        }).trim();
        return { success: true, name: safeName, remaining: parseInt(output, 10) || 0 };
      }
      return { success: false, error: 'Missing pid or name' };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  spawnProcess(command, args = []) {
    try {
      if (!command) return { success: false, error: 'Missing command' };
      const safeCommand = String(command).replace(/[;&|`$(){}!#<>]/g, '');
      if (!safeCommand) return { success: false, error: 'Invalid command' };
      const argList = Array.isArray(args) ? args.map(a => String(a)) : [];
      const child = spawn(safeCommand, argList, {
        detached: true,
        stdio: 'ignore',
        shell: false,
      });
      child.unref();
      return { success: true, pid: child.pid, command: safeCommand, args: argList };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  getProcessInfo(pid, name) {
    try {
      const safeName = this._escapePS(name);
      const filter = pid ? `-Id ${Number(pid)}` : `-Name '${safeName}' -ErrorAction SilentlyContinue`;
      const script = `Get-Process ${filter} | Select-Object Id,ProcessName,CPU,WorkingSet64,StartTime,Path,CommandLine | ConvertTo-Json -Compress`;
      const output = execSync('powershell -NoProfile -Command -', {
        input: script,
        encoding: 'utf-8',
        timeout: 5000,
        windowsHide: true,
      }).trim();
      if (!output) return { success: false, error: 'Process not found' };
      const data = JSON.parse(output);
      return {
        success: true,
        pid: data.Id,
        name: data.ProcessName,
        cpu_percent: data.CPU ? Math.round(data.CPU * 100) / 100 : 0,
        memory_bytes: data.WorkingSet64 || 0,
        memory_mb: Math.round((data.WorkingSet64 || 0) / 1048576 * 100) / 100,
        start_time: data.StartTime || null,
        path: data.Path || null,
      };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  monitorProcesses() {
    try {
      const script = `Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 20 Id,ProcessName,CPU,WorkingSet64 | ConvertTo-Json -Compress`;
      const output = execSync('powershell -NoProfile -Command -', {
        input: script,
        encoding: 'utf-8',
        timeout: 10000,
        windowsHide: true,
      }).trim();
      if (!output) return { success: true, processes: [] };
      const data = JSON.parse(output);
      const processes = (Array.isArray(data) ? data : [data]).map(p => ({
        pid: p.Id,
        name: p.ProcessName,
        cpu_percent: p.CPU ? Math.round(p.CPU * 100) / 100 : 0,
        memory_bytes: p.WorkingSet64 || 0,
        memory_mb: Math.round((p.WorkingSet64 || 0) / 1048576 * 100) / 100,
      }));
      return {
        success: true,
        processes,
        total_cpu: os.cpus().length > 0 ? processes.reduce((s, p) => s + p.cpu_percent, 0) : 0,
        total_memory_bytes: processes.reduce((s, p) => s + p.memory_bytes, 0),
        system_memory: {
          total_gb: Math.round(os.totalmem() / 1073741824 * 100) / 100,
          free_gb: Math.round(os.freemem() / 1073741824 * 100) / 100,
        },
      };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }
}

module.exports = { DesktopProcessManager };
