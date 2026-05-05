chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'polyspace-summarize',
    title: 'PolySpace: 总结选中内容',
    contexts: ['selection'],
  });
  chrome.contextMenus.create({
    id: 'polyspace-translate',
    title: 'PolySpace: 翻译选中内容',
    contexts: ['selection'],
  });
  chrome.contextMenus.create({
    id: 'polyspace-explain',
    title: 'PolySpace: 解释选中内容',
    contexts: ['selection'],
  });
  chrome.contextMenus.create({
    id: 'polyspace-capture',
    title: 'PolySpace: 保存页面到知识库',
    contexts: ['page'],
  });
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  const serverUrl = (await chrome.storage.local.get('serverUrl')).serverUrl || 'http://localhost:8000';
  const apiKey = (await chrome.storage.local.get('apiKey')).apiKey || '';

  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (apiKey) headers['Authorization'] = `Bearer ${apiKey}`;

  if (info.menuItemId === 'polyspace-summarize' && info.selectionText) {
    await fetch(`${serverUrl}/api/v1/chat/message`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ message: `请总结以下内容：\n\n${info.selectionText}`, action: 'summarize' }),
    });
  } else if (info.menuItemId === 'polyspace-translate' && info.selectionText) {
    await fetch(`${serverUrl}/api/v1/chat/message`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ message: `请翻译以下内容为中文：\n\n${info.selectionText}`, action: 'translate' }),
    });
  } else if (info.menuItemId === 'polyspace-explain' && info.selectionText) {
    await fetch(`${serverUrl}/api/v1/chat/message`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ message: `请解释以下内容：\n\n${info.selectionText}`, action: 'explain' }),
    });
  } else if (info.menuItemId === 'polyspace-capture' && tab) {
    const title = tab.title || '';
    const url = tab.url || '';
    await fetch(`${serverUrl}/api/v1/clipboard/clipboard`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ content: `[${title}](${url})`, source_device: 'chrome-extension' }),
    });
  }
});

chrome.action.onClicked.addListener((tab) => {
  chrome.sidePanel.open({ tabId: tab.id });
});
