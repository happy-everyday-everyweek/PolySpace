const { execSync, spawn } = require('child_process');
const os = require('os');

class DesktopWindowManager {
  constructor() {
    this._toolDefinition = {
      name: 'desktop_window',
      description: 'Desktop window management - list, focus, minimize, maximize, close, screenshot',
      actions: ['list', 'focus', 'minimize', 'maximize', 'close', 'get_active', 'screenshot', 'move', 'resize'],
    };
  }

  getCapabilities() {
    return [{
      name: this._toolDefinition.name,
      description: this._toolDefinition.description,
      actions: this._toolDefinition.actions,
      parameters: {
        action: { type: 'string', description: 'Action to perform' },
        window_id: { type: 'string', description: 'Window identifier' },
        title: { type: 'string', description: 'Window title to find' },
        x: { type: 'integer', description: 'Window X position' },
        y: { type: 'integer', description: 'Window Y position' },
        width: { type: 'integer', description: 'Window width' },
        height: { type: 'integer', description: 'Window height' },
      },
    }];
  }

  async executeAction(action, params = {}) {
    switch (action) {
      case 'list':
        return this.listWindows();
      case 'focus':
        return this.focusWindow(params.window_id, params.title);
      case 'minimize':
        return this.minimizeWindow(params.window_id, params.title);
      case 'maximize':
        return this.maximizeWindow(params.window_id, params.title);
      case 'close':
        return this.closeWindow(params.window_id, params.title);
      case 'get_active':
        return this.getActiveWindow();
      case 'screenshot':
        return this.screenshotWindow(params.window_id, params.title);
      case 'move':
        return this.moveWindow(params.window_id, params.x, params.y);
      case 'resize':
        return this.resizeWindow(params.window_id, params.width, params.height);
      default:
        throw new Error(`Unknown action: ${action}`);
    }
  }

  _runPowershell(script) {
    try {
      const result = execSync('powershell -NoProfile -Command -', {
        input: script,
        encoding: 'utf-8',
        timeout: 10000,
        windowsHide: true,
      });
      return result.trim();
    } catch (e) {
      return null;
    }
  }

  _escapePS(str) {
    return String(str || '').replace(/'/g, "''");
  }

  listWindows() {
    const script = `
      Add-Type @"
      using System;
      using System.Runtime.InteropServices;
      public class WinAPI {
        public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
        [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc proc, IntPtr lParam);
        [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
        [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder text, int count);
        [DllImport("user32.dll")] public static extern int GetWindowTextLength(IntPtr hWnd);
        [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
      }
"@
      $results = @()
      [WinAPI]::EnumWindows({
        param($hWnd, $lParam)
        if ([WinAPI]::IsWindowVisible($hWnd)) {
          $len = [WinAPI]::GetWindowTextLength($hWnd)
          if ($len -gt 0) {
            $sb = New-Object System.Text.StringBuilder($len + 1)
            [WinAPI]::GetWindowText($hWnd, $sb, $sb.Capacity) | Out-Null
            $title = $sb.ToString()
            if ($title -ne '') {
              $results += @{id=$hWnd.ToString();title=$title}
            }
          }
        }
        return $true
      }, [IntPtr]::Zero) | Out-Null
      $results | ConvertTo-Json -Compress
    `;
    const output = this._runPowershell(script);
    if (!output) return { success: false, error: 'Failed to list windows' };
    try {
      const windows = JSON.parse(output);
      const list = Array.isArray(windows) ? windows : [windows];
      return { success: true, windows: list, count: list.length };
    } catch (e) {
      return { success: false, error: 'Failed to parse window list' };
    }
  }

  focusWindow(windowId, title) {
    if (windowId) {
      const script = `Add-Type "using System;using System.Runtime.InteropServices;public class W{[DllImport(\\"user32.dll\\")]public static extern bool SetForegroundWindow(IntPtr h);}"; [W]::SetForegroundWindow([IntPtr]::new(${Number(windowId)}))`;
      const result = this._runPowershell(script);
      return { success: result !== null, window_id: windowId };
    }
    if (title) {
      const safeTitle = this._escapePS(title);
      const script = `
        Add-Type "using System;using System.Runtime.InteropServices;public class W{[DllImport(\\"user32.dll\\")]public static extern bool SetForegroundWindow(IntPtr h);[DllImport(\\"user32.dll\\",CharSet=CharSet.Unicode)]public static extern int FindWindow(string c,string t);}"
        $h = [W]::FindWindow($null,'${safeTitle}')
        if ($h -ne 0) { [W]::SetForegroundWindow([IntPtr]::new($h)); 'ok' } else { 'not_found' }
      `;
      const result = this._runPowershell(script);
      return { success: result === 'ok', title };
    }
    return { success: false, error: 'Missing window_id or title' };
  }

  minimizeWindow(windowId, title) {
    const id = windowId || '0';
    const safeTitle = this._escapePS(title);
    const script = `
      Add-Type "using System;using System.Runtime.InteropServices;public class W{[DllImport(\\"user32.dll\\")]public static extern bool ShowWindow(IntPtr h,int c);}"
      $h = if ('${id}' -ne '0') { [IntPtr]::new(${Number(id)}) } else { (Get-Process | Where-Object {$_.MainWindowTitle -eq '${safeTitle}'})[0].MainWindowHandle }
      if ($h -and $h -ne [IntPtr]::Zero) { [W]::ShowWindow($h, 6); 'ok' } else { 'not_found' }
    `;
    const result = this._runPowershell(script);
    return { success: result === 'ok' };
  }

  maximizeWindow(windowId, title) {
    const id = windowId || '0';
    const safeTitle = this._escapePS(title);
    const script = `
      Add-Type "using System;using System.Runtime.InteropServices;public class W{[DllImport(\\"user32.dll\\")]public static extern bool ShowWindow(IntPtr h,int c);}"
      $h = if ('${id}' -ne '0') { [IntPtr]::new(${Number(id)}) } else { (Get-Process | Where-Object {$_.MainWindowTitle -eq '${safeTitle}'})[0].MainWindowHandle }
      if ($h -and $h -ne [IntPtr]::Zero) { [W]::ShowWindow($h, 3); 'ok' } else { 'not_found' }
    `;
    const result = this._runPowershell(script);
    return { success: result === 'ok' };
  }

  closeWindow(windowId, title) {
    const id = windowId || '0';
    const safeTitle = this._escapePS(title);
    const script = `
      Add-Type "using System;using System.Runtime.InteropServices;public class W{[DllImport(\\"user32.dll\\")]public static extern bool PostMessage(IntPtr h,uint m,IntPtr w,IntPtr l);}"
      $h = if ('${id}' -ne '0') { [IntPtr]::new(${Number(id)}) } else { (Get-Process | Where-Object {$_.MainWindowTitle -eq '${safeTitle}'})[0].MainWindowHandle }
      if ($h -and $h -ne [IntPtr]::Zero) { [W]::PostMessage($h, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero); 'ok' } else { 'not_found' }
    `;
    const result = this._runPowershell(script);
    return { success: result === 'ok' };
  }

  getActiveWindow() {
    const script = `
      Add-Type "using System;using System.Runtime.InteropServices;public class W{[DllImport(\\"user32.dll\\")]public static extern IntPtr GetForegroundWindow();[DllImport(\\"user32.dll\\",CharSet=CharSet.Unicode)]public static extern int GetWindowText(IntPtr h,System.Text.StringBuilder t,int c);}"
      $h = [W]::GetForegroundWindow()
      $sb = New-Object System.Text.StringBuilder(256)
      [W]::GetWindowText($h, $sb, 256) | Out-Null
      @{id=$h.ToString();title=$sb.ToString()} | ConvertTo-Json -Compress
    `;
    const output = this._runPowershell(script);
    if (!output) return { success: false, error: 'Failed to get active window' };
    try {
      return { success: true, ...JSON.parse(output) };
    } catch (e) {
      return { success: false, error: 'Failed to parse active window info' };
    }
  }

  screenshotWindow(windowId, title) {
    return { success: false, error: 'Use screen_operation screenshot action instead' };
  }

  moveWindow(windowId, x, y) {
    if (!windowId) return { success: false, error: 'Missing window_id' };
    const wid = Number(windowId);
    if (!Number.isFinite(wid)) return { success: false, error: 'Invalid window_id' };
    const script = `
      Add-Type "using System;using System.Runtime.InteropServices;public class W{[DllImport(\\"user32.dll\\")]public static extern bool MoveWindow(IntPtr h,int x,int y,int w,int hp,bool r);[DllImport(\\"user32.dll\\")]public static extern bool GetWindowRect(IntPtr h,out RECT r);public struct RECT{public int L,T,R,B;}}"
      $h = [IntPtr]::new(${wid})
      $r = New-Object W+RECT
      [W]::GetWindowRect($h,[ref]$r) | Out-Null
      [W]::MoveWindow($h,${Number(x) || 0},${Number(y) || 0},$r.R-$r.L,$r.B-$r.T,$true); 'ok'
    `;
    const result = this._runPowershell(script);
    return { success: result === 'ok' };
  }

  resizeWindow(windowId, width, height) {
    if (!windowId) return { success: false, error: 'Missing window_id' };
    const wid = Number(windowId);
    if (!Number.isFinite(wid)) return { success: false, error: 'Invalid window_id' };
    const script = `
      Add-Type "using System;using System.Runtime.InteropServices;public class W{[DllImport(\\"user32.dll\\")]public static extern bool MoveWindow(IntPtr h,int x,int y,int w,int hp,bool r);[DllImport(\\"user32.dll\\")]public static extern bool GetWindowRect(IntPtr h,out RECT r);public struct RECT{public int L,T,R,B;}}"
      $h = [IntPtr]::new(${wid})
      $r = New-Object W+RECT
      [W]::GetWindowRect($h,[ref]$r) | Out-Null
      [W]::MoveWindow($h,$r.L,$r.T,${Number(width) || 800},${Number(height) || 600},$true); 'ok'
    `;
    const result = this._runPowershell(script);
    return { success: result === 'ok' };
  }
}

module.exports = { DesktopWindowManager };
