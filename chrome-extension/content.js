(function () {
  let floatingBtn = null;

  function createFloatingButton() {
    if (floatingBtn) return;
    floatingBtn = document.createElement('button');
    floatingBtn.className = 'polyspace-floating-btn';
    floatingBtn.textContent = 'P';
    floatingBtn.title = 'PolySpace AI Assistant';
    floatingBtn.addEventListener('click', () => {
      chrome.runtime.sendMessage({ action: 'openSidePanel' });
    });
    document.body.appendChild(floatingBtn);
  }

  function removeFloatingButton() {
    if (floatingBtn) {
      floatingBtn.remove();
      floatingBtn = null;
    }
  }

  function getSelectedText() {
    return window.getSelection()?.toString() || '';
  }

  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.action === 'getSelectedText') {
      sendResponse({ text: getSelectedText() });
    } else if (msg.action === 'getPageContent') {
      sendResponse({
        title: document.title,
        url: window.location.href,
        content: document.body.innerText.substring(0, 5000),
      });
    } else if (msg.action === 'showFloatingButton') {
      createFloatingButton();
    } else if (msg.action === 'hideFloatingButton') {
      removeFloatingButton();
    }
  });

  createFloatingButton();
})();
