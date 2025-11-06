const toggle = document.getElementById('toggle');
const autoCloseToggle = document.getElementById('autoClose');
const statusText = document.getElementById('status');

const DEFAULT_SETTINGS = {
  enabled: true,
  autoCloseIrrelevant: true,
};

const formatStatusMessage = ({ enabled, autoCloseIrrelevant }) => {
  if (!enabled) {
    return 'Automation is paused';
  }
  return autoCloseIrrelevant
    ? 'Automation is enabled; tabs auto-close when no action is taken'
    : 'Automation is enabled; tabs stay open when no action is taken';
};

const updateStatusLabel = (settings) => {
  statusText.textContent = formatStatusMessage(settings);
};

chrome.storage.local.get(DEFAULT_SETTINGS, (settings) => {
  const mergedSettings = {
    enabled: Boolean(settings.enabled),
    autoCloseIrrelevant: Boolean(
      Object.prototype.hasOwnProperty.call(settings, 'autoCloseIrrelevant')
        ? settings.autoCloseIrrelevant
        : DEFAULT_SETTINGS.autoCloseIrrelevant,
    ),
  };

  toggle.checked = mergedSettings.enabled;
  autoCloseToggle.checked = mergedSettings.autoCloseIrrelevant;
  updateStatusLabel(mergedSettings);
});

toggle.addEventListener('change', () => {
  const nextSettings = {
    enabled: toggle.checked,
    autoCloseIrrelevant: autoCloseToggle.checked,
  };

  chrome.storage.local.set({ enabled: nextSettings.enabled });
  updateStatusLabel(nextSettings);
});

autoCloseToggle.addEventListener('change', () => {
  const nextSettings = {
    enabled: toggle.checked,
    autoCloseIrrelevant: autoCloseToggle.checked,
  };

  chrome.storage.local.set({ autoCloseIrrelevant: nextSettings.autoCloseIrrelevant });
  updateStatusLabel(nextSettings);
});
