(() => {
  console.log('Script de prospection LinkedIn chargé !');
  
  const checkAndConnect = () => {
    // PRIORITY 1: Try to follow company first (Suivre button)
    const followButton = Array.from(document.querySelectorAll('button.follow'))
      .find(btn => btn.getAttribute('aria-label') === 'Suivre');

    if (followButton && !followButton.disabled) {
      followButton.click();
      console.log("✅ Bouton Suivre (company) cliqué - priorité 1.");
      chrome.runtime.sendMessage({action: "close_tab"});
      return;
    }

    // Try alternative follow button selector for companies
    const followButtonAlt = Array.from(document.querySelectorAll('button'))
      .find(btn => {
        const text = btn.textContent?.trim();
        return text === 'Suivre' && btn.classList.contains('follow');
      });

    if (followButtonAlt && !followButtonAlt.disabled) {
      followButtonAlt.click();
      console.log("✅ Bouton Suivre alternatif (company) cliqué - priorité 1.");
      chrome.runtime.sendMessage({action: "close_tab"});
      return;
    }

    // Try broader follow button detection for companies
    const followButtonBroad = Array.from(document.querySelectorAll('button'))
      .find(btn => {
        const text = btn.textContent?.trim();
        const ariaLabel = btn.getAttribute('aria-label');
        return text === 'Suivre' || 
               (ariaLabel && ariaLabel.includes('Suivre'));
      });

    if (followButtonBroad && !followButtonBroad.disabled) {
      followButtonBroad.click();
      console.log("✅ Bouton Suivre général (company) cliqué - priorité 1.");
      chrome.runtime.sendMessage({action: "close_tab"});
      return;
    }

    // PRIORITY 2: If no company follow button found, try to connect with employee
    const connectButton = Array.from(document.querySelectorAll('button'))
      .find(btn => {
        const text = btn.textContent?.trim();
        const ariaLabel = btn.getAttribute('aria-label');
        return text === 'Se connecter' || 
               (ariaLabel && ariaLabel.includes('rejoindre votre réseau'));
      });

    if (connectButton && !connectButton.disabled) {
      connectButton.click();
      console.log("✅ Bouton Se connecter (employee) cliqué - priorité 2.");
      
      // Wait for modal to appear and click "Envoyer sans note"
      setTimeout(() => {
        const sendWithoutNoteButton = Array.from(document.querySelectorAll('button'))
          .find(btn => {
            const text = btn.textContent?.trim();
            const ariaLabel = btn.getAttribute('aria-label');
            return text === 'Envoyer sans note' || 
                   (ariaLabel && ariaLabel.includes('Envoyer sans note'));
          });
        
        if (sendWithoutNoteButton && !sendWithoutNoteButton.disabled) {
          sendWithoutNoteButton.click();
          console.log("✅ Invitation envoyée sans note.");
          
          // Close tab after sending invitation
          setTimeout(() => {
            chrome.runtime.sendMessage({action: "close_tab"});
          }, 1000);
        } else {
          console.log("⚠️ Bouton 'Envoyer sans note' non trouvé, fermeture du tab.");
          chrome.runtime.sendMessage({action: "close_tab"});
        }
      }, 2000); // Wait 2 seconds for modal to load
      
      return;
    }

    // If neither button found, wait and retry
    console.log("⏳ Aucun bouton trouvé (ni Suivre ni Se connecter), nouvelle tentative dans 1 seconde...");
    setTimeout(checkAndConnect, 1000);
  };

  // Start the automation after page loads
  checkAndConnect();
})();