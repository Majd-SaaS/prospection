(() => {
  const LOG_PREFIX = '[LinkedIn Auto Follow]';
  const MAX_ATTEMPTS = 10;
  const RETRY_DELAY_MS = 1000;

  const closeTab = () => {
    chrome.runtime.sendMessage({ action: 'close_tab' });
  };

  const storageGet = (keys) => new Promise((resolve) => {
    chrome.storage.local.get(keys, (result) => {
      if (chrome.runtime.lastError) {
        console.warn(`${LOG_PREFIX} Unable to read extension settings, defaulting to enabled.`, chrome.runtime.lastError);
        const fallbackEnabled = typeof keys === 'object' && keys !== null && Object.prototype.hasOwnProperty.call(keys, 'enabled')
          ? keys.enabled
          : true;
        resolve({ enabled: fallbackEnabled });
        return;
      }

      resolve(result);
    });
  });

  const isExtensionEnabled = async () => {
    const result = await storageGet({ enabled: true });
    return Boolean(result.enabled);
  };

  const isEnglishUi = () => {
    const lang = (document.documentElement.getAttribute('lang') || '').toLowerCase();
    return !lang || lang.startsWith('en');
  };

  const isCompanyPage = () => {
    const currentUrl = window.location.href;
    if (currentUrl.includes('/company/')) {
      return true;
    }

    const canonicalLink = document.querySelector('link[rel="canonical"]');
    return Boolean(canonicalLink && canonicalLink.href.includes('/company/'));
  };

  const isFollowButton = (btn) => {
    if (!btn || btn.disabled) {
      return false;
    }

    const ariaPressed = btn.getAttribute('aria-pressed');
    if (ariaPressed && ariaPressed.toLowerCase() === 'true') {
      return false;
    }

    const text = (btn.textContent || '').trim().toLowerCase();
    const ariaLabel = (btn.getAttribute('aria-label') || '').trim().toLowerCase();
    const controlName = (btn.getAttribute('data-control-name') || '').trim().toLowerCase();
    const spanTexts = Array.from(btn.querySelectorAll('span'))
      .map((span) => (span.textContent || '').trim().toLowerCase())
      .filter(Boolean);

    const followSynonyms = ['follow', 'follow company'];
    const buttonTexts = [text, ...spanTexts];
    const hasFollowText = buttonTexts.some((value) => followSynonyms.includes(value));
    const hasFollowLabel = ariaLabel.includes('follow') && !ariaLabel.includes('following');
    const hasFollowControl = controlName.includes('follow');

    const alreadyFollowingText = buttonTexts.some((value) => value.includes('following'));
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
    console.log(`${LOG_PREFIX} Attempt ${attempt}: searching for a Follow button on the company page...`);

    const followButton = findFollowButton();

    if (followButton) {
      followButton.click();
      console.log(`${LOG_PREFIX} Follow button clicked successfully.`);
      setTimeout(closeTab, 1000);
      return;
    }

    if (attempt >= MAX_ATTEMPTS) {
      console.log(`${LOG_PREFIX} Unable to locate a Follow button after multiple attempts. Closing tab.`);
      closeTab();
      return;
    }

    console.log(`${LOG_PREFIX} Follow button not found yet. Retrying shortly...`);
    setTimeout(() => tryFollowCompany(attempt + 1), RETRY_DELAY_MS);
  };

  const startAutomation = async () => {
    if (!(await isExtensionEnabled())) {
      console.log(`${LOG_PREFIX} Automation is disabled via the popup toggle.`);
      return;
    }

    if (!isEnglishUi()) {
      console.log(`${LOG_PREFIX} Non-English LinkedIn interface detected. Closing tab to prevent unintended actions.`);
      closeTab();
      return;
    }

    if (!isCompanyPage()) {
      console.log(`${LOG_PREFIX} Non-company page detected. Closing tab without action.`);
      closeTab();
      return;
    }

    if (window.location.href.includes('unavailable')) {
      console.log(`${LOG_PREFIX} Unavailable LinkedIn page detected. Closing tab.`);
      closeTab();
      return;
    }

    setTimeout(() => tryFollowCompany(), 500);
  };

  const runAutomation = () => {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', startAutomation, { once: true });
    } else {
      startAutomation();
    }
  };

  const automationApi = {
    LOG_PREFIX,
    MAX_ATTEMPTS,
    RETRY_DELAY_MS,
    closeTab,
    storageGet,
    isExtensionEnabled,
    isEnglishUi,
    isCompanyPage,
    isFollowButton,
    findFollowButton,
    tryFollowCompany,
    startAutomation,
    runAutomation,
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = automationApi;
  } else {
    runAutomation();
  }
})();
