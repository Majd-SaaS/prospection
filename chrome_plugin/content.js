(() => {
  const LOG_PREFIX = '[LinkedIn Auto Follow]';
  const MAX_ATTEMPTS = 10;
  const RETRY_DELAY_MS = 1000;
  const FOLLOW_CONFIRM_ATTEMPTS = 6;
  const FOLLOW_CONFIRM_DELAY_MS = 500;
  const DEFAULT_SETTINGS = {
    enabled: true,
    autoCloseIrrelevant: true,
  };
  const DEFAULT_PAGE_DURATION = 60;

  const closeTab = () => {
    chrome.runtime.sendMessage({ action: 'close_tab' });
  };

  const storageGet = (keys) =>
    new Promise((resolve) => {
      chrome.storage.local.get(keys, (result) => {
        if (chrome.runtime.lastError) {
          console.warn(
            `${LOG_PREFIX} Unable to read extension settings. Falling back to defaults.`,
            chrome.runtime.lastError,
          );
          resolve(keys);
          return;
        }

        resolve(result);
      });
    });

  const getExtensionSettings = async () => {
    const settings = await storageGet(DEFAULT_SETTINGS);
    return {
      enabled: Boolean(settings.enabled),
      autoCloseIrrelevant: Boolean(
        Object.prototype.hasOwnProperty.call(settings, 'autoCloseIrrelevant')
          ? settings.autoCloseIrrelevant
          : DEFAULT_SETTINGS.autoCloseIrrelevant,
      ),
    };
  };

  const parseProspectionTracking = () => {
    const response = {
      port: null,
      taskId: null,
      hasTracking: false,
      pageDuration: DEFAULT_PAGE_DURATION,
    };

    const extractFromWindowName = () => {
      if (!window.name || !window.name.startsWith('prospection::')) {
        return false;
      }
      try {
        const raw = window.name.slice('prospection::'.length);
        const payload = JSON.parse(raw);
        if (payload && payload.port && payload.task_id) {
          response.port = Number(payload.port);
          response.taskId = payload.task_id;
          if (payload.page_duration !== undefined) {
            const duration = Number(payload.page_duration);
            response.pageDuration = Number.isFinite(duration) ? Math.max(0, duration) : DEFAULT_PAGE_DURATION;
          }
          response.hasTracking = true;
          return true;
        }
      } catch (error) {
        console.warn(`${LOG_PREFIX} Unable to parse tracking data from window.name.`, error);
      }
      return false;
    };

    const extractFromHash = () => {
      try {
        const hash = window.location.hash.startsWith('#')
          ? window.location.hash.slice(1)
          : window.location.hash;
        const params = new URLSearchParams(hash);
        const port = params.get('prospection_port');
        const taskId = params.get('prospection_task_id');
        if (port && taskId) {
          response.port = Number(port);
          response.taskId = taskId;
          response.pageDuration = DEFAULT_PAGE_DURATION;
          response.hasTracking = true;
          return true;
        }
      } catch (error) {
        console.warn(`${LOG_PREFIX} Unable to parse tracking fragment.`, error);
      }
      return false;
    };

    if (extractFromWindowName()) {
      return response;
    }
    extractFromHash(); // fallback for backwards compatibility
    return response;
  };

  const trackingConfig = parseProspectionTracking();
  let hasReported = false;

  const reportResult = async (status, reason = '') => {
    if (!trackingConfig.hasTracking) {
      return false;
    }

    const payload = {
      action: 'report_result',
      port: trackingConfig.port,
      taskId: trackingConfig.taskId,
      url: window.location.href.split('#')[0],
      status,
      reason,
    };

    return new Promise((resolve) => {
      chrome.runtime.sendMessage(payload, (response) => {
        if (chrome.runtime.lastError) {
          console.warn(`${LOG_PREFIX} Unable to send result to the CLI.`, chrome.runtime.lastError);
          resolve(false);
          return;
        }
        resolve(Boolean(response?.ok));
      });
    });
  };

  const reportOnce = async (status, reason = '') => {
    if (!trackingConfig.hasTracking || hasReported) {
      return;
    }
    hasReported = true;
    await reportResult(status, reason);
  };

  const isEnglishUi = () => {
    const lang = (document.documentElement.getAttribute('lang') || '').toLowerCase();
    return !lang || lang.startsWith('en') || lang.startsWith('fr');
  };

  const isCompanyPage = () => {
    const currentUrl = window.location.href;
    if (currentUrl.includes('/company/')) {
      return true;
    }

    const canonicalLink = document.querySelector('link[rel="canonical"]');
    return Boolean(canonicalLink && canonicalLink.href.includes('/company/'));
  };

  const detectLoginForm = () => {
    return Boolean(
      document.querySelector("input[name='session_key']") ||
        document.querySelector("form[action*='login']"),
    );
  };

  const collectButtonTexts = (btn) => {
    const text = (btn.textContent || '').trim().toLowerCase();
    const spanTexts = Array.from(btn.querySelectorAll('span'))
      .map((span) => (span.textContent || '').trim().toLowerCase())
      .filter(Boolean);
    return [text, ...spanTexts].filter(Boolean);
  };

  const classifyButtonState = (btn) => {
    if (!btn || btn.disabled) {
      return 'unknown';
    }

    const ariaPressed = btn.getAttribute('aria-pressed');
    if (ariaPressed && ariaPressed.toLowerCase() === 'true') {
      return 'already followed';
    }

    const ariaLabel = (btn.getAttribute('aria-label') || '').trim().toLowerCase();
    const controlName = (btn.getAttribute('data-control-name') || '').trim().toLowerCase();
    const buttonTexts = collectButtonTexts(btn);

    const followSynonyms = ['follow', 'follow company', 'suivre'];
    const followingKeywords = ['following', 'abonné', 'abonnée'];

    const hasFollowText = buttonTexts.some((value) => followSynonyms.includes(value));
    const hasFollowLabel = ariaLabel.includes('follow') && !ariaLabel.includes('following');
    const hasFollowControl = controlName.includes('follow');

    const alreadyFollowingText = buttonTexts.some((value) =>
      followingKeywords.some((keyword) => value.includes(keyword)),
    );
    const alreadyFollowingLabel = ariaLabel.includes('following') || ariaLabel.includes('abonné');

    if (alreadyFollowingText || alreadyFollowingLabel) {
      return 'already followed';
    }

    if (hasFollowText || hasFollowLabel || hasFollowControl) {
      return 'follow';
    }

    return 'unknown';
  };

  const isFollowButton = (btn) => classifyButtonState(btn) === 'follow';

  const findButtonByState = (states) => {
    const prioritizedSelectors = [
      'button.follow',
      'button[data-control-name="follow"]',
      'button[data-test-id="follow-button"]',
      'button[data-test-follow-button]',
      'button[aria-label*="Follow"]',
    ];

    for (const selector of prioritizedSelectors) {
      const button = Array.from(document.querySelectorAll(selector)).find((candidate) =>
        states.has(classifyButtonState(candidate)),
      );
      if (button) {
        return button;
      }
    }

    return (
      Array.from(document.querySelectorAll('button')).find((candidate) =>
        states.has(classifyButtonState(candidate)),
      ) || null
    );
  };

  const findFollowButton = () => findButtonByState(new Set(['follow']));
  const findFollowRelatedButton = () => findButtonByState(new Set(['follow', 'already followed']));

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  const confirmFollowSucceeded = async () => {
    for (let attempt = 1; attempt <= FOLLOW_CONFIRM_ATTEMPTS; attempt += 1) {
      const button = findFollowRelatedButton();
      const state = classifyButtonState(button);
      if (state === 'already followed') {
        return true;
      }
      if (state === 'follow' && attempt > 1) {
        return false;
      }
      await sleep(FOLLOW_CONFIRM_DELAY_MS);
    }
    return false;
  };

  const finalizeAutomation = async (
    settings,
    status,
    reason = '',
    closeTabImmediately = true,
    dueToIrrelevant = false,
  ) => {
    await reportOnce(status, reason);
    const shouldClose = closeTabImmediately || (dueToIrrelevant && settings.autoCloseIrrelevant);
    if (shouldClose) {
      const durationSeconds = Math.max(0, trackingConfig.pageDuration || DEFAULT_PAGE_DURATION);
      const performClose = () => {
        if (window.name && window.name.startsWith('prospection::')) {
          window.name = '';
        }
        closeTab();
      };

      if (durationSeconds > 0) {
        setTimeout(performClose, durationSeconds * 1000);
      } else {
        performClose();
      }
    }
  };

  const tryFollowCompany = async (settings, attempt = 1) => {
    const followButton = findFollowButton();

    if (followButton) {
      const state = classifyButtonState(followButton);
      if (state === 'already followed') {
        await finalizeAutomation(settings, 'already followed');
        return;
      }

      followButton.click();
      console.log(`${LOG_PREFIX} Follow button clicked. Waiting for confirmation...`);
      const succeeded = await confirmFollowSucceeded();
      if (succeeded) {
        await finalizeAutomation(settings, 'follow');
      } else {
        await finalizeAutomation(
          settings,
          'error',
          'Unable to confirm follow action.',
          false,
          true,
        );
      }
      return;
    }

    if (attempt >= MAX_ATTEMPTS) {
      await finalizeAutomation(
        settings,
        'error',
        'Follow button not found.',
        false,
        true,
      );
      return;
    }

    setTimeout(() => {
      tryFollowCompany(settings, attempt + 1);
    }, RETRY_DELAY_MS);
  };

  const startAutomation = async () => {
    const settings = await getExtensionSettings();

    if (!settings.enabled) {
      await reportOnce('skipped', 'Extension toggle is disabled.');
      return;
    }

    if (window.location.href.includes('unavailable')) {
      await finalizeAutomation(settings, 'error', 'LinkedIn page unavailable.', true, true);
      return;
    }

    if (!isEnglishUi()) {
      await finalizeAutomation(settings, 'error', 'Unsupported LinkedIn language.', true, true);
      return;
    }

    if (!isCompanyPage()) {
      await finalizeAutomation(settings, 'error', 'Not a company page.', false, true);
      return;
    }

    if (detectLoginForm()) {
      await finalizeAutomation(
        settings,
        'error',
        'LinkedIn redirected to a login form.',
        true,
        true,
      );
      return;
    }

    tryFollowCompany(settings);
  };

  const runAutomation = () => {
    if (document.readyState === 'loading') {
      document.addEventListener(
        'DOMContentLoaded',
        () => {
          startAutomation().catch((error) =>
            console.error(`${LOG_PREFIX} Automation failed.`, error),
          );
        },
        { once: true },
      );
    } else {
      startAutomation().catch((error) =>
        console.error(`${LOG_PREFIX} Automation failed.`, error),
      );
    }
  };

  const automationApi = {
    LOG_PREFIX,
    MAX_ATTEMPTS,
    RETRY_DELAY_MS,
    FOLLOW_CONFIRM_ATTEMPTS,
    FOLLOW_CONFIRM_DELAY_MS,
    DEFAULT_SETTINGS,
    DEFAULT_PAGE_DURATION,
    closeTab,
    storageGet,
    getExtensionSettings,
    parseProspectionTracking,
    reportResult,
    reportOnce,
    isEnglishUi,
    isCompanyPage,
    classifyButtonState,
    isFollowButton,
    findFollowButton,
    findFollowRelatedButton,
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
