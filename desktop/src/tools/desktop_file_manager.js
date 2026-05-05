const fs = require('fs');
const path = require('path');
const os = require('os');

const fsp = fs.promises;

class DesktopFileManager {
  constructor() {
    this._toolDefinition = {
      name: 'desktop_file',
      description: 'Desktop file operations - read, write, list, copy, move, delete, search',
      actions: ['read', 'write', 'list', 'delete', 'copy', 'move', 'exists', 'mkdir', 'stat', 'search'],
    };
  }

  getCapabilities() {
    return [{
      name: this._toolDefinition.name,
      description: this._toolDefinition.description,
      actions: this._toolDefinition.actions,
      parameters: {
        action: { type: 'string', description: 'Action to perform' },
        path: { type: 'string', description: 'File or directory path' },
        content: { type: 'string', description: 'Content to write' },
        destination: { type: 'string', description: 'Destination path' },
        recursive: { type: 'boolean', description: 'Recursive operation' },
        pattern: { type: 'string', description: 'Glob pattern for search' },
        encoding: { type: 'string', description: 'File encoding (default: utf-8)' },
      },
    }];
  }

  async executeAction(action, params = {}) {
    switch (action) {
      case 'read':
        return this.readFile(params.path, params.encoding);
      case 'write':
        return this.writeFile(params.path, params.content, params.encoding);
      case 'list':
        return this.listDir(params.path, params.recursive);
      case 'delete':
        return this.deletePath(params.path, params.recursive);
      case 'copy':
        return this.copyPath(params.path, params.destination);
      case 'move':
        return this.movePath(params.path, params.destination);
      case 'exists':
        return this.existsPath(params.path);
      case 'mkdir':
        return this.makeDir(params.path, params.recursive);
      case 'stat':
        return this.statPath(params.path);
      case 'search':
        return this.searchFiles(params.path, params.pattern);
      default:
        throw new Error(`Unknown action: ${action}`);
    }
  }

  async readFile(filePath, encoding = 'utf-8') {
    try {
      if (!filePath) return { success: false, error: 'Missing path' };
      const resolved = path.resolve(filePath);
      const [content, stat] = await Promise.all([
        fsp.readFile(resolved, encoding),
        fsp.stat(resolved),
      ]);
      return {
        success: true,
        content,
        size: stat.size,
        modified: stat.mtime.toISOString(),
        encoding,
      };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  async writeFile(filePath, content, encoding = 'utf-8') {
    try {
      if (!filePath) return { success: false, error: 'Missing path' };
      const resolved = path.resolve(filePath);
      const dir = path.dirname(resolved);
      await fsp.mkdir(dir, { recursive: true });
      await fsp.writeFile(resolved, content, encoding);
      return { success: true, path: resolved, size: Buffer.byteLength(content, encoding) };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  async listDir(dirPath, recursive = false) {
    try {
      if (!dirPath) return { success: false, error: 'Missing path' };
      const resolved = path.resolve(dirPath);

      let stat;
      try {
        stat = await fsp.stat(resolved);
      } catch (_) {
        return { success: false, error: 'Path does not exist' };
      }
      if (!stat.isDirectory()) return { success: false, error: 'Path is not a directory' };

      const entries = await this._listDirRecursive(resolved, recursive);
      return { success: true, path: resolved, entries, count: entries.length };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  async _listDirRecursive(dir, recursive) {
    const entries = [];
    const items = await fsp.readdir(dir, { withFileTypes: true });
    for (const item of items) {
      const fullPath = path.join(dir, item.name);
      let itemStat;
      try {
        itemStat = await fsp.stat(fullPath);
      } catch (_) {
        continue;
      }
      entries.push({
        name: item.name,
        path: fullPath,
        is_directory: item.isDirectory(),
        size: itemStat.size,
        modified: itemStat.mtime.toISOString(),
      });
      if (recursive && item.isDirectory()) {
        const subEntries = await this._listDirRecursive(fullPath, true);
        entries.push(...subEntries);
      }
    }
    return entries;
  }

  _isSafePath(targetPath) {
    const resolved = path.resolve(targetPath).toLowerCase();
    const home = os.homedir().toLowerCase();
    const unsafePrefixes = [
      'c:\\windows',
      'c:\\program files',
      'c:\\program files (x86)',
      'c:\\programdata',
      'c:\\users\\public',
      'c:\\$recycle.bin',
      'c:\\system volume information',
    ];
    for (const prefix of unsafePrefixes) {
      if (resolved.startsWith(prefix)) return false;
    }
    if (resolved.length <= 3) return false;
    return true;
  }

  async deletePath(targetPath, recursive = false) {
    try {
      if (!targetPath) return { success: false, error: 'Missing path' };
      const resolved = path.resolve(targetPath);

      if (!this._isSafePath(resolved)) {
        return { success: false, error: 'Cannot delete system paths or protected directories' };
      }

      let stat;
      try {
        stat = await fsp.stat(resolved);
      } catch (_) {
        return { success: false, error: 'Path does not exist' };
      }
      if (stat.isDirectory()) {
        await fsp.rm(resolved, { recursive: !!recursive, force: false });
      } else {
        await fsp.unlink(resolved);
      }
      return { success: true, path: resolved };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  async copyPath(srcPath, destPath) {
    try {
      if (!srcPath || !destPath) return { success: false, error: 'Missing source or destination' };
      const src = path.resolve(srcPath);
      const dest = path.resolve(destPath);

      let stat;
      try {
        stat = await fsp.stat(src);
      } catch (_) {
        return { success: false, error: 'Source does not exist' };
      }
      if (stat.isDirectory()) {
        await fsp.cp(src, dest, { recursive: true });
      } else {
        const destDir = path.dirname(dest);
        await fsp.mkdir(destDir, { recursive: true });
        await fsp.copyFile(src, dest);
      }
      return { success: true, source: src, destination: dest };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  async movePath(srcPath, destPath) {
    try {
      if (!srcPath || !destPath) return { success: false, error: 'Missing source or destination' };
      const src = path.resolve(srcPath);
      const dest = path.resolve(destPath);

      try {
        await fsp.access(src);
      } catch (_) {
        return { success: false, error: 'Source does not exist' };
      }
      const destDir = path.dirname(dest);
      await fsp.mkdir(destDir, { recursive: true });
      await fsp.rename(src, dest);
      return { success: true, source: src, destination: dest };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  async existsPath(targetPath) {
    try {
      if (!targetPath) return { success: false, error: 'Missing path' };
      const resolved = path.resolve(targetPath);
      try {
        const stat = await fsp.stat(resolved);
        return {
          success: true,
          exists: true,
          is_directory: stat.isDirectory(),
          is_file: stat.isFile(),
          size: stat.size,
          modified: stat.mtime.toISOString(),
        };
      } catch (_) {
        return { success: true, exists: false };
      }
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  async makeDir(dirPath, recursive = true) {
    try {
      if (!dirPath) return { success: false, error: 'Missing path' };
      const resolved = path.resolve(dirPath);
      await fsp.mkdir(resolved, { recursive: !!recursive });
      return { success: true, path: resolved };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  async statPath(targetPath) {
    try {
      if (!targetPath) return { success: false, error: 'Missing path' };
      const resolved = path.resolve(targetPath);
      let stat;
      try {
        stat = await fsp.stat(resolved);
      } catch (_) {
        return { success: false, error: 'Path does not exist' };
      }
      return {
        success: true,
        path: resolved,
        is_directory: stat.isDirectory(),
        is_file: stat.isFile(),
        size: stat.size,
        created: stat.birthtime.toISOString(),
        modified: stat.mtime.toISOString(),
        accessed: stat.atime.toISOString(),
        mode: stat.mode.toString(8),
      };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  async searchFiles(dirPath, pattern = '*') {
    try {
      if (!dirPath) return { success: false, error: 'Missing path' };
      const resolved = path.resolve(dirPath);
      try {
        await fsp.access(resolved);
      } catch (_) {
        return { success: false, error: 'Path does not exist' };
      }

      const results = [];
      const regex = this._globToRegex(pattern);
      await this._searchRecursive(resolved, regex, results, 0, 5);
      return { success: true, path: resolved, pattern, results, count: results.length };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  _globToRegex(pattern) {
    if (!pattern || pattern === '*') return /.*/;
    const escaped = pattern
      .replace(/[.+^${}()|[\]\\]/g, '\\$&')
      .replace(/\*/g, '.*')
      .replace(/\?/g, '.');
    return new RegExp(`^${escaped}$`, 'i');
  }

  async _searchRecursive(dir, regex, results, depth, maxDepth) {
    if (depth > maxDepth) return;
    try {
      const items = await fsp.readdir(dir, { withFileTypes: true });
      for (const item of items) {
        if (regex.test(item.name)) {
          const fullPath = path.join(dir, item.name);
          try {
            const stat = await fsp.stat(fullPath);
            results.push({
              name: item.name,
              path: fullPath,
              is_directory: item.isDirectory(),
              size: stat.size,
            });
          } catch (_) {}
        }
        if (item.isDirectory()) {
          await this._searchRecursive(path.join(dir, item.name), regex, results, depth + 1, maxDepth);
        }
      }
    } catch (_) {}
  }
}

module.exports = { DesktopFileManager };
