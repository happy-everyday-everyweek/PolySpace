const WebSocket = require('ws');

class DeviceBridgeClient {
  constructor(backendUrl, deviceId, deviceName, platform, capabilities) {
    this._backendUrl = backendUrl;
    this._deviceId = deviceId || this._generateDeviceId();
    this._deviceName = deviceName || `windows-${this._deviceId.slice(0, 8)}`;
    this._platform = platform || 'windows';
    this._capabilities = capabilities || [];
    this._ws = null;
    this._connected = false;
    this._reconnectAttempts = 0;
    this._maxReconnectAttempts = 10;
    this._reconnectInterval = 3000;
    this._heartbeatInterval = 15000;
    this._heartbeatTimer = null;
    this._toolExecutor = null;
    this._onConnected = null;
    this._onDisconnected = null;
    this._onCommand = null;
  }

  _generateDeviceId() {
    const os = require('os');
    const hostname = os.hostname();
    const crypto = require('crypto');
    return crypto.createHash('sha256').update(hostname).digest('hex');
  }

  setToolExecutor(executor) {
    this._toolExecutor = executor;
  }

  setCallbacks(onConnected, onDisconnected, onCommand) {
    this._onConnected = onConnected;
    this._onDisconnected = onDisconnected;
    this._onCommand = onCommand;
  }

  get deviceId() { return this._deviceId; }
  get connected() { return this._connected; }

  connect() {
    if (this._ws) {
      try { this._ws.removeAllListeners(); this._ws.close(); } catch (_) {}
      this._ws = null;
    }

    const wsUrl = `${this._backendUrl}/api/v1/devices/ws/${this._deviceId}`;
    console.log(`[DeviceBridge] Connecting to ${wsUrl}`);

    try {
      this._ws = new WebSocket(wsUrl);
    } catch (e) {
      console.error(`[DeviceBridge] Failed to create WebSocket: ${e.message}`);
      this._scheduleReconnect();
      return;
    }

    this._ws.on('open', () => {
      console.log('[DeviceBridge] WebSocket connected');
      this._connected = true;
      this._reconnectAttempts = 0;

      this._send({
        device_name: this._deviceName,
        platform: this._platform,
        capabilities: this._capabilities,
        metadata: {
          hostname: require('os').hostname(),
          platform: require('os').platform(),
          arch: require('os').arch(),
        }
      });

      this._startHeartbeat();

      if (this._onConnected) {
        this._onConnected();
      }
    });

    this._ws.on('message', (data) => {
      try {
        const message = JSON.parse(data.toString());
        this._handleMessage(message);
      } catch (e) {
        console.error(`[DeviceBridge] Failed to parse message: ${e.message}`);
      }
    });

    this._ws.on('close', (code, reason) => {
      console.log(`[DeviceBridge] WebSocket closed: ${code} ${reason}`);
      this._onDisconnect();
    });

    this._ws.on('error', (error) => {
      console.error(`[DeviceBridge] WebSocket error: ${error.message}`);
      this._onDisconnect();
    });
  }

  _onDisconnect() {
    this._connected = false;
    this._stopHeartbeat();

    if (this._onDisconnected) {
      this._onDisconnected();
    }

    this._scheduleReconnect();
  }

  _scheduleReconnect() {
    if (this._reconnectAttempts >= this._maxReconnectAttempts) {
      console.error(`[DeviceBridge] Max reconnect attempts reached (${this._maxReconnectAttempts})`);
      return;
    }

    const delay = this._reconnectInterval * Math.pow(1.5, this._reconnectAttempts);
    this._reconnectAttempts++;

    console.log(`[DeviceBridge] Reconnecting in ${Math.round(delay)}ms (attempt ${this._reconnectAttempts}/${this._maxReconnectAttempts})`);

    setTimeout(() => {
      this.connect();
    }, delay);
  }

  _startHeartbeat() {
    this._stopHeartbeat();
    this._heartbeatTimer = setInterval(() => {
      this._send({ type: 'heartbeat' });
    }, this._heartbeatInterval);
  }

  _stopHeartbeat() {
    if (this._heartbeatTimer) {
      clearInterval(this._heartbeatTimer);
      this._heartbeatTimer = null;
    }
  }

  _send(data) {
    if (this._ws && this._ws.readyState === WebSocket.OPEN) {
      this._ws.send(JSON.stringify(data));
    }
  }

  async _handleMessage(message) {
    const msgType = message.type || '';

    switch (msgType) {
      case 'register_ack':
        console.log(`[DeviceBridge] Registration acknowledged, tools: ${JSON.stringify(message.registered_tools || [])}`);
        break;

      case 'heartbeat_ack':
        break;

      case 'tool_call': {
        const requestId = message.request_id;
        const tool = message.tool;
        const action = message.action;
        const params = message.params || {};

        console.log(`[DeviceBridge] Tool call: ${tool}/${action} (request: ${requestId})`);

        try {
          let result;
          if (this._toolExecutor) {
            result = await this._toolExecutor(tool, action, params);
          } else if (this._onCommand) {
            result = await this._onCommand(tool, action, params);
          } else {
            result = { error: 'No tool executor configured' };
          }

          this._send({
            type: 'tool_result',
            request_id: requestId,
            result: result,
          });
        } catch (e) {
          this._send({
            type: 'tool_error',
            request_id: requestId,
            error: e.message,
          });
        }
        break;
      }

      case 'disconnect':
        console.log(`[DeviceBridge] Server requested disconnect: ${message.reason || ''}`);
        this.disconnect();
        break;

      default:
        console.log(`[DeviceBridge] Unknown message type: ${msgType}`);
    }
  }

  sendCapabilityUpdate(capabilities) {
    this._capabilities = capabilities;
    this._send({
      type: 'capability_update',
      capabilities: capabilities,
    });
  }

  sendStatusUpdate(status) {
    this._send({
      type: 'status_update',
      status: status,
    });
  }

  disconnect() {
    this._stopHeartbeat();
    this._reconnectAttempts = this._maxReconnectAttempts;
    if (this._ws) {
      try {
        this._send({ type: 'disconnect', reason: 'client_shutdown' });
        this._ws.close();
      } catch (e) {
        // ignore
      }
      this._ws = null;
    }
    this._connected = false;
  }
}

module.exports = { DeviceBridgeClient };
