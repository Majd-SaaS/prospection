(async () => {
  const reportResult = async (payload) => {
    const { port, taskId, url, status, reason = '' } = payload;
    if (!port || !taskId || !url || !status) {
      throw new Error('Missing reporting fields.');
    }

    const endpoint = `http://127.0.0.1:${port}/report`;
    await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        task_id: taskId,
        url,
        status,
        reason,
      }),
      keepalive: true,
    });
  };

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'close_tab' && sender.tab?.id) {
      chrome.tabs.remove(sender.tab.id);
      return;
    }

    if (message.action === 'report_result') {
      reportResult(message)
        .then(() => sendResponse({ ok: true }))
        .catch((error) => {
          console.warn('[LinkedIn Auto Follow] Failed to report result.', error);
          sendResponse({ ok: false, error: error?.message || 'unknown error' });
        });
      return true; // keep the message channel open for async response
    }
  });
})();
