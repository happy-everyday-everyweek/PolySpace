const os = require('os');
const { execSync } = require('child_process');

class DesktopSystemManager {
  constructor() {
    this._toolDefinition = {
      name: 'desktop_system',
      description: 'Desktop system information - CPU, memory, disk, network, environment',
      actions: ['cpu_info', 'memory_info', 'disk_info', 'network_info', 'env_info', 'os_info', 'uptime', 'battery_info'],
    };
  }

  getCapabilities() {
    return [{
      name: this._toolDefinition.name,
      description: this._toolDefinition.description,
      actions: this._toolDefinition.actions,
      parameters: {
        action: { type: 'string', description: 'Action to perform' },
        drive: { type: 'string', description: 'Drive letter (Windows)' },
        interface: { type: 'string', description: 'Network interface name' },
      },
    }];
  }

  async executeAction(action, params = {}) {
    switch (action) {
      case 'cpu_info':
        return this.cpuInfo();
      case 'memory_info':
        return this.memoryInfo();
      case 'disk_info':
        return this.diskInfo(params.drive);
      case 'network_info':
        return this.networkInfo(params.interface);
      case 'env_info':
        return this.envInfo();
      case 'os_info':
        return this.osInfo();
      case 'uptime':
        return this.uptimeInfo();
      case 'battery_info':
        return this.batteryInfo();
      default:
        throw new Error(`Unknown action: ${action}`);
    }
  }

  cpuInfo() {
    const cpus = os.cpus();
    return {
      success: true,
      model: cpus[0]?.model || 'unknown',
      cores: cpus.length,
      speed_mhz: cpus[0]?.speed || 0,
      architecture: os.arch(),
      load_avg: os.loadavg ? os.loadavg().map(v => Math.round(v * 100) / 100) : [],
    };
  }

  memoryInfo() {
    const total = os.totalmem();
    const free = os.freemem();
    const used = total - free;
    return {
      success: true,
      total_bytes: total,
      total_gb: Math.round(total / 1073741824 * 100) / 100,
      used_bytes: used,
      used_gb: Math.round(used / 1073741824 * 100) / 100,
      free_bytes: free,
      free_gb: Math.round(free / 1073741824 * 100) / 100,
      usage_percent: Math.round(used / total * 10000) / 100,
    };
  }

  diskInfo(drive) {
    try {
      const driveLetter = (drive || 'C').replace(/[^A-Za-z]/g, '').charAt(0).toUpperCase();
      const script = `Get-PSDrive -Name '${driveLetter}' | Select-Object Used,Free | ConvertTo-Json -Compress`;
      const output = execSync('powershell -NoProfile -Command -', {
        input: script,
        encoding: 'utf-8',
        timeout: 5000,
        windowsHide: true,
      }).trim();
      const data = JSON.parse(output);
      const used = data.Used || 0;
      const free = data.Free || 0;
      const total = used + free;
      return {
        success: true,
        drive: driveLetter,
        total_bytes: total,
        total_gb: Math.round(total / 1073741824 * 100) / 100,
        used_bytes: used,
        used_gb: Math.round(used / 1073741824 * 100) / 100,
        free_bytes: free,
        free_gb: Math.round(free / 1073741824 * 100) / 100,
        usage_percent: total > 0 ? Math.round(used / total * 10000) / 100 : 0,
      };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  networkInfo(iface) {
    const interfaces = os.networkInterfaces();
    const result = {};
    for (const [name, addrs] of Object.entries(interfaces)) {
      if (iface && name !== iface) continue;
      result[name] = addrs.map(a => ({
        address: a.address,
        netmask: a.netmask,
        family: a.family,
        internal: a.internal,
        mac: a.mac,
      }));
    }
    return {
      success: true,
      interfaces: result,
      hostname: os.hostname(),
    };
  }

  envInfo() {
    const env = process.env;
    const filtered = {};
    const safeKeys = [
      'PATH', 'HOME', 'USERPROFILE', 'APPDATA', 'TEMP', 'TMP',
      'COMPUTERNAME', 'USERNAME', 'USERDOMAIN', 'OS',
      'PROCESSOR_ARCHITECTURE', 'NUMBER_OF_PROCESSORS',
      'LANG', 'SHELL', 'TERM', 'EDITOR',
    ];
    for (const key of safeKeys) {
      if (env[key]) filtered[key] = env[key];
    }
    return { success: true, environment: filtered };
  }

  osInfo() {
    return {
      success: true,
      platform: os.platform(),
      release: os.release(),
      version: os.version ? os.version() : '',
      arch: os.arch(),
      hostname: os.hostname(),
      user: os.userInfo().username,
      homedir: os.homedir(),
      tmpdir: os.tmpdir(),
      endianness: os.endianness(),
    };
  }

  uptimeInfo() {
    const uptime = os.uptime();
    const hours = Math.floor(uptime / 3600);
    const minutes = Math.floor((uptime % 3600) / 60);
    const seconds = Math.floor(uptime % 60);
    return {
      success: true,
      uptime_seconds: uptime,
      uptime_formatted: `${hours}h ${minutes}m ${seconds}s`,
    };
  }

  batteryInfo() {
    try {
      const script = `Get-CimInstance Win32_Battery | Select-Object EstimatedChargeRemaining,BatteryStatus,EstimatedChargeRemaining | ConvertTo-Json -Compress`;
      const output = execSync('powershell -NoProfile -Command -', {
        input: script,
        encoding: 'utf-8',
        timeout: 5000,
        windowsHide: true,
      }).trim();
      if (!output || output === '') {
        return { success: true, has_battery: false };
      }
      const data = JSON.parse(output);
      const statusMap = { 1: 'discharging', 2: 'ac_power', 3: 'fully_charged', 4: 'low', 5: 'critical' };
      return {
        success: true,
        has_battery: true,
        charge_percent: data.EstimatedChargeRemaining || 0,
        status: statusMap[data.BatteryStatus] || 'unknown',
      };
    } catch (e) {
      return { success: true, has_battery: false, error: e.message };
    }
  }
}

module.exports = { DesktopSystemManager };
