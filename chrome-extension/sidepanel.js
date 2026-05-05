document.addEventListener('DOMContentLoaded', async () => {
  const messagesEl = document.getElementById('messages');
  const inputEl = document.getElementById('input') as HTMLInputElement;
  const sendBtn = document.getElementById('send');

  const { serverUrl, apiKey } = await chrome.storage.local.get(['serverUrl', 'apiKey']);
  const baseUrl = serverUrl || 'http://localhost:8000';
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (apiKey) headers['Authorization'] = `Bearer ${apiKey}`;

  function addMessage(role: string, content: string) {
    const div = document.createElement('div');
    div.className = `msg ${role}`;
    div.textContent = content;
    messagesEl?.appendChild(div);
    messagesEl?.scrollTo(0, messagesEl.scrollHeight);
  }

  async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text) return;
    addMessage('user', text);
    inputEl.value = '';
    sendBtn!.setAttribute('disabled', 'true');
    try {
      const resp = await fetch(`${baseUrl}/api/v1/chat/message`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ message: text }),
      });
      const data = await resp.json();
      addMessage('assistant', data.response || data.message || JSON.stringify(data));
    } catch (e) {
      addMessage('assistant', '连接失败，请检查服务器设置');
    }
    sendBtn!.removeAttribute('disabled');
  }

  sendBtn?.addEventListener('click', sendMessage);
  inputEl?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  addMessage('assistant', '你好！我是 PolySpace AI 助手，有什么可以帮你的？');
});
