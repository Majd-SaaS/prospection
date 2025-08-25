(() => {
  console.log('Script de prospection LinkedIn chargé !');
  
  const checkAndConnect = () => {
    const currentUrl = window.location.href;
    
    // Check if URL contains 'unavailable' and close tab immediately
    if (currentUrl.includes('unavailable')) {
      console.log("❌ Page indisponible détectée, fermeture immédiate du tab.");
      chrome.runtime.sendMessage({action: "close_tab"});
      return;
    }
    
    const isCompanyPage = currentUrl.includes('/company/');
    
    if (isCompanyPage) {
      console.log("📄 Page entreprise détectée, recherche du bouton Suivre...");
      
      // PRIORITY 1: Try to follow company (Suivre button) - only on company pages
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
      
      // If no follow button found on company page, log and retry
      console.log("⏳ Aucun bouton Suivre trouvé sur la page entreprise, nouvelle tentative dans 1 seconde...");
      setTimeout(checkAndConnect, 1000);
      return;
    }
    
    // PRIORITY 2: For non-company pages (employee profiles), try to connect
    const connectButton = Array.from(document.querySelectorAll('button'))
      .find(btn => {
        const text = btn.textContent?.trim();
        const ariaLabel = btn.getAttribute('aria-label');
        const spanText = btn.querySelector('span.artdeco-button__text')?.textContent?.trim();
        
        // Check for "Se connecter" text in button content or spans
        const hasConnectText = text === 'Se connecter' || spanText === 'Se connecter';
        
        // Check for aria-label patterns
        const hasConnectAriaLabel = ariaLabel && (
          ariaLabel.includes('rejoindre votre réseau') ||
          ariaLabel.includes('Invitez') ||
          ariaLabel.toLowerCase().includes('connect')
        );
        
        // Check if it's a primary artdeco button (typical for connect buttons)
        const isPrimaryButton = btn.classList.contains('artdeco-button--primary');
        
        return hasConnectText || (hasConnectAriaLabel && isPrimaryButton);
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

    // If no connect button found on employee profile, wait and retry
    console.log("👤 Page profil détectée - ⏳ Aucun bouton Se connecter trouvé, nouvelle tentative dans 1 seconde...");
    setTimeout(checkAndConnect, 1000);
  };

  // Start the automation after page loads
  checkAndConnect();
})();