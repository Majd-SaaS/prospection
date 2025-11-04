## Add the extension to Chrome

This extension automatically clicks the English "Follow" button on LinkedIn company pages.
It works best when combined with the automated company opener in the CLI utilities and is disabled on non-English interfaces.

Steps:
- Open `chrome://extensions/` in Chrome.
- Enable **Developer mode**.
- Click **Load unpacked** and select the `chrome_plugin` folder from this repository.
- Confirm the installation, then open the extension popup to ensure the toggle is **enabled**.

When the toggle is off, the content script will leave LinkedIn untouched. On non-company pages or non-English profiles, the tab closes automatically without clicking anything.
