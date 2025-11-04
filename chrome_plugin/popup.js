const toggle = document.getElementById('toggle');
const statusText = document.getElementById('status');

const updateStatusLabel = (isEnabled) => {
  statusText.textContent = isEnabled ? 'Automation is enabled' : 'Automation is paused';
};

chrome.storage.local.get({ enabled: true }, ({ enabled }) => {
  const isEnabled = Boolean(enabled);
  toggle.checked = isEnabled;
  updateStatusLabel(isEnabled);
});

toggle.addEventListener('change', () => {
  const isEnabled = toggle.checked;
  chrome.storage.local.set({ enabled: isEnabled });
  updateStatusLabel(isEnabled);
});
