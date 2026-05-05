document.addEventListener('DOMContentLoaded', async () => {
  const statusEl = document.getElementById('status');
  const serverUrlInput = document.getElementById('server-url') as HTMLInputElement;
  const apiKeyInput = document.getElementById('api-key') as HTMLInputElement;

  const { serverUrl, apiKey } = await chrome.storage.local.get(['serverUrl', 'apiKey']);
  serverUrlInput.value = serverUrl || 'http://localhost:8000';
  apiKeyInput.value = apiKey || '';

  async function checkConnection() {
    const url = serverUrlInput.value || 'http://localhost:8000';
    try {
      const resp = await fetch(`${url}/api/v1/health`, { method: 'GET', signal: AbortSignal.timeout(3000) });
      if (resp.ok) {
        statusEl.textContent = '已连接';
        statusEl.className = 'popup-status connected';
      } else {
        statusEl.textContent = '连接失败';
        statusEl.className = 'popup-status disconnected';
      }
    } catch {
      statusEl.textContent = '无法连接到服务器';
      statusEl.className = 'popup-status disconnected';
    }
  }

  checkConnection();

  document.getElementById('save-settings')?.addEventListener('click', async () => {
    await chrome.storage.local.set({
      serverUrl: serverUrlInput.value,
      apiKey: apiKeyInput.value,
    });
    checkConnection();
  });

  async function getHeaders() {
    const key = apiKeyInput.value || (await chrome.storage.local.get('apiKey')).apiKey || '';
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (key) headers['Authorization'] = `Bearer ${key}`;
    return headers;
  }

  document.getElementById('btn-summarize')?.addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) return;
    const results = await chrome.scripting.executeScript({ target: { tabId: tab.id! }, func: () => document.body.innerText.substring(0, 5000) });
    const content = results?.[0]?.result || '';
    const url = serverUrlInput.value || 'http://localhost:8000';
    await fetch(`${url}/api/v1/chat/message`, {
      method: 'POST',
      headers: await getHeaders(),
      body: JSON.stringify({ message: `请总结以下页面内容：\n\n${content}` }),
    });
  });

  document.getElementById('btn-translate')?.addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) return;
    const results = await chrome.scripting.executeScript({ target: { tabId: tab.id! }, func: () => window.getSelection()?.toString() || '' });
    const text = results?.[0]?.result || '';
    if (!text) { alert('请先选中要翻译的文本'); return; }
    const url = serverUrlInput.value || 'http://localhost:8000';
    await fetch(`${url}/api/v1/chat/message`, {
      method: 'POST',
      headers: await getHeaders(),
      body: JSON.stringify({ message: `请翻译以下内容为中文：\n\n${text}` }),
    });
  });

  document.getElementById('btn-explain')?.addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) return;
    const results = await chrome.scripting.executeScript({ target: { tabId: tab.id! }, func: () => window.getSelection()?.toString() || '' });
    const text = results?.[0]?.result || '';
    if (!text) { alert('请先选中要解释的文本'); return; }
    const url = serverUrlInput.value || 'http://localhost:8000';
    await fetch(`${url}/api/v1/chat/message`, {
      method: 'POST',
      headers: await getHeaders(),
      body: JSON.stringify({ message: `请解释以下内容：\n\n${text}` }),
    });
  });

  document.getElementById('btn-capture')?.addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) return;
    const url = serverUrlInput.value || 'http://localhost:8000';
    await fetch(`${url}/api/v1/clipboard/clipboard`, {
      method: 'POST',
      headers: await getHeaders(),
      body: JSON.stringify({ content: `[${tab.title}](${tab.url})`, source_device: 'chrome-extension' }),
    });
  });

  document.getElementById('btn-chat')?.addEventListener('click', async () => {
    chrome.sidePanel.open({ windowId: (await chrome.windows.getCurrent()).id });
  });
});
