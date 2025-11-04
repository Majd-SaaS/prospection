(() => {
  console.log('LinkedIn company follow automation loaded.');

  const MAX_ATTEMPTS = 10;
  const RETRY_DELAY_MS = 1000;

  const closeTab = () => {
    chrome.runtime.sendMessage({ action: 'close_tab' });
  };

  const isFollowButton = (btn) => {
    if (!btn || btn.disabled) {
      return false;
    }

    const ariaPressed = btn.getAttribute('aria-pressed');
    if (ariaPressed && ariaPressed.toLowerCase() === 'true') {
      return false; // already following
    }

    const text = (btn.textContent || '').trim().toLowerCase();
    const ariaLabel = (btn.getAttribute('aria-label') || '').trim().toLowerCase();
    const controlName = (btn.getAttribute('data-control-name') || '').trim().toLowerCase();
    const spanTexts = Array.from(btn.querySelectorAll('span'))
      .map((span) => (span.textContent || '').trim().toLowerCase())
      .filter(Boolean);

    const hasFollowText = text === 'follow' || spanTexts.includes('follow');
    const hasFollowLabel = ariaLabel.includes('follow') && !ariaLabel.includes('following');
    const hasFollowControl = controlName.includes('follow');

    const alreadyFollowingText = text.includes('following') || spanTexts.some((t) => t.includes('following'));
    const alreadyFollowingLabel = ariaLabel.includes('following');

    return !alreadyFollowingText && !alreadyFollowingLabel && (hasFollowText || hasFollowLabel || hasFollowControl);
  };

  const findFollowButton = () => {
    const prioritizedSelectors = [
      'button.follow',
      'button[data-control-name="follow"]',
      'button[data-test-id="follow-button"]',
    ];

    for (const selector of prioritizedSelectors) {
      const button = Array.from(document.querySelectorAll(selector)).find(isFollowButton);
      if (button) {
        return button;
      }
    }

    return Array.from(document.querySelectorAll('button')).find(isFollowButton) || null;
  };

  const tryFollowCompany = (attempt = 1) => {
    const currentUrl = window.location.href;

    if (currentUrl.includes('unavailable')) {
      console.log('Unavailable LinkedIn page detected. Closing tab immediately.');
      closeTab();
      return;
    }

    if (!currentUrl.includes('/company/')) {
      console.log('Non-company page detected. No action will be taken.');
      closeTab();
      return;
    }

    console.log(`Attempt ${attempt}: searching for a Follow button on the company page...`);

    const followButton = findFollowButton();

    if (followButton) {
      followButton.click();
      console.log('Follow button clicked successfully.');
      setTimeout(closeTab, 1000);
      return;
    }

    if (attempt >= MAX_ATTEMPTS) {
      console.log('Unable to locate a Follow button after multiple attempts. Closing tab.');
      closeTab();
      return;
    }

    console.log('Follow button not found yet. Retrying shortly...');
    setTimeout(() => tryFollowCompany(attempt + 1), RETRY_DELAY_MS);
  };

  // Start the automation shortly after the page loads
  setTimeout(() => tryFollowCompany(), 500);
})();
