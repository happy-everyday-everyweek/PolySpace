const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

function getRecordingsDir() {
  const dir = path.join(os.homedir(), 'PolySpace', 'recordings');
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  return dir;
}

class ScreenRecorderManager {
  constructor() {
    this._ffmpegProcess = null;
    this._isRecording = false;
    this._isPaused = false;
    this._outputPath = '';
    this._startTime = 0;
    this._ffmpegAvailable = null;
    this._checkPromise = null;
  }

  get isRecording() { return this._isRecording; }
  get isPaused() { return this._isPaused; }
  get outputPath() { return this._outputPath; }

  async checkFFmpeg() {
    if (this._ffmpegAvailable !== null) return this._ffmpegAvailable;
    if (this._checkPromise) return this._checkPromise;

    this._checkPromise = new Promise((resolve) => {
      const proc = spawn('ffmpeg', ['-version']);
      let settled = false;
      const settle = (val) => {
        if (settled) return;
        settled = true;
        this._ffmpegAvailable = val;
        this._checkPromise = null;
        resolve(val);
      };
      const timer = setTimeout(() => {
        try { proc.kill(); } catch (_) {}
        settle(false);
      }, 5000);
      proc.on('error', () => { clearTimeout(timer); settle(false); });
      proc.on('close', (code) => { clearTimeout(timer); settle(code === 0); });
    });

    return this._checkPromise;
  }

  async startRecording(options = {}) {
    if (this._isRecording) return { success: false, error: 'Already recording' };

    const available = await this.checkFFmpeg();
    if (!available) return { success: false, error: 'FFmpeg not available' };

    const recordingsDir = getRecordingsDir();

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `desktop_${timestamp}.mp4`;
    this._outputPath = path.join(recordingsDir, filename);

    const quality = options.quality || 'high';
    const fps = options.fps || 30;
    const includeAudio = options.includeAudio !== false;

    const qualityPresets = {
      low: { crf: 28, preset: 'fast' },
      medium: { crf: 23, preset: 'medium' },
      high: { crf: 18, preset: 'slow' },
      original: { crf: 15, preset: 'veryslow' },
    };
    const preset = qualityPresets[quality] || qualityPresets.high;

    const args = ['-y'];

    if (includeAudio) {
      args.push(
        '-f', 'dshow',
        '-i', 'audio=virtual-audio-capturer',
      );
    }

    args.push(
      '-f', 'gdigrab',
      '-framerate', String(fps),
      '-offset_x', String(options.x || 0),
      '-offset_y', String(options.y || 0),
      '-video_size', options.resolution || '1920x1080',
      '-i', 'desktop',
    );

    args.push(
      '-c:v', 'libx264',
      '-crf', String(preset.crf),
      '-preset', preset.preset,
      '-pix_fmt', 'yuv420p',
    );

    if (includeAudio) {
      args.push('-c:a', 'aac', '-b:a', '128k');
    }

    args.push(this._outputPath);

    try {
      this._ffmpegProcess = spawn('ffmpeg', args, {
        stdio: ['pipe', 'pipe', 'pipe'],
        windowsHide: true,
      });

      this._ffmpegProcess.stderr.on('data', () => {});

      this._ffmpegProcess.on('error', (err) => {
        console.error('FFmpeg process error:', err);
        this._isRecording = false;
        this._ffmpegProcess = null;
      });

      this._ffmpegProcess.on('close', () => {
        this._isRecording = false;
        this._isPaused = false;
        this._ffmpegProcess = null;
      });

      this._isRecording = true;
      this._isPaused = false;
      this._startTime = Date.now();

      return {
        success: true,
        output_path: this._outputPath,
        quality,
        fps,
        include_audio: includeAudio,
      };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  async stopRecording() {
    if (!this._isRecording || !this._ffmpegProcess) {
      return { success: false, error: 'Not recording' };
    }

    const duration = Math.floor((Date.now() - this._startTime) / 1000);
    const outputPath = this._outputPath;
    const proc = this._ffmpegProcess;

    return new Promise((resolve) => {
      const timeout = setTimeout(() => {
        try { proc.kill(); } catch (_) {}
        this._isRecording = false;
        this._isPaused = false;
        this._ffmpegProcess = null;
        resolve({ success: false, error: 'FFmpeg did not stop in time', output_path: outputPath, duration });
      }, 5000);

      proc.on('close', () => {
        clearTimeout(timeout);
        this._isRecording = false;
        this._isPaused = false;
        this._ffmpegProcess = null;
        resolve({ success: true, output_path: outputPath, duration });
      });

      try {
        proc.stdin.write('q');
      } catch (e) {
        clearTimeout(timeout);
        try { proc.kill(); } catch (_) {}
        this._isRecording = false;
        this._isPaused = false;
        this._ffmpegProcess = null;
        resolve({ success: false, error: e.message });
      }
    });
  }

  pauseRecording() {
    if (!this._isRecording || this._isPaused) return { success: false, error: 'Cannot pause' };
    try {
      this._ffmpegProcess.stdin.write('p');
      this._isPaused = true;
      return { success: true, paused: true };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  resumeRecording() {
    if (!this._isRecording || !this._isPaused) return { success: false, error: 'Cannot resume' };
    try {
      this._ffmpegProcess.stdin.write('p');
      this._isPaused = false;
      return { success: true, paused: false };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  getStatus() {
    const duration = this._isRecording ? Math.floor((Date.now() - this._startTime) / 1000) : 0;
    return {
      recording: this._isRecording,
      paused: this._isPaused,
      output_path: this._outputPath,
      duration,
    };
  }

  async takeScreenshot(options = {}) {
    const available = await this.checkFFmpeg();
    if (!available) return { success: false, error: 'FFmpeg not available' };

    const recordingsDir = getRecordingsDir();

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const screenshotPath = path.join(recordingsDir, `screenshot_${timestamp}.png`);

    const args = [
      '-y',
      '-f', 'gdigrab',
      '-video_size', options.resolution || '1920x1080',
      '-i', 'desktop',
      '-vframes', '1',
      screenshotPath,
    ];

    return new Promise((resolve) => {
      const proc = spawn('ffmpeg', args, { windowsHide: true });
      proc.on('close', (code) => {
        if (code === 0 && fs.existsSync(screenshotPath)) {
          resolve({ success: true, path: screenshotPath });
        } else {
          resolve({ success: false, error: 'Screenshot failed' });
        }
      });
      proc.on('error', (err) => resolve({ success: false, error: err.message }));
    });
  }
}

module.exports = { ScreenRecorderManager };
