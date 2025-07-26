// content.js - Fixed version
(function() {
  'use strict';

  // Get Firebase config from background script
  chrome.runtime.sendMessage({ action: 'getFirebaseConfig' }, (response) => {
    if (!response || !response.config) {
      console.error('Failed to get Firebase config');
      return;
    }
    
    const firebaseConfig = response.config;
    const databaseURL = firebaseConfig.databaseURL;
    
    const safeURLs = [
      "https://www.instagram.com/accounts/login/",
      "https://accounts.google.com/",
      "https://www.facebook.com/login/",
      "https://www.linkedin.com/login",
      "https://twitter.com/login",
      "subhadra_odisha_gov_in",
      "https://github.com/login"
    ];

    const sensitiveKeywords = ["password", "username", "userid", "user id", "id", "aadhaar", "adhar", "user_name"];
    let lastCheckedURL = "";

    // Firebase REST API functions
    async function getVoteCount(hostname) {
      try {
        const sanitizedHostname = hostname.replace(/[.#$[\]]/g, '_');
        const response = await fetch(`${databaseURL}/userAddedUrls/${sanitizedHostname}.json`);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data || 0;
      } catch (error) {
        console.error('Error getting vote count:', error);
        return 0;
      }
    }
    // Function to increment user votes in databse
    async function incrementVote(hostname) {
      try {
        const sanitizedHostname = hostname.replace(/[.#$[\]]/g, '_');
        
        // Get current count first
        const response = await fetch(`${databaseURL}/userAddedUrls/${sanitizedHostname}.json`);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const currentCount = await response.json() || 0;
        const newCount = currentCount + 1;
        
        // Attempt to update with exact +1 increment
        const updateResponse = await fetch(`${databaseURL}/userAddedUrls/${sanitizedHostname}.json`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newCount)
        });
        
        if (!updateResponse.ok) {
          // Check if it's a Firebase rules violation
          const error = await updateResponse.text();
          if (updateResponse.status === 400 && error.includes('permission_denied')) {
            throw new Error('Vote rejected by security rules - possible concurrent voting');
          }
          throw new Error(`HTTP error! status: ${updateResponse.status}`);
        }
        
        return newCount;
      } catch (error) {
        console.error('Error incrementing vote:', error);
        return null;
      }
    }


    function checkForPhishing() {
      const currentURL = window.location.href;
      if (currentURL === lastCheckedURL) return;
      lastCheckedURL = currentURL;
      
      const inputs = Array.from(document.querySelectorAll("input"));
      const hasSensitiveInput = inputs.some(input => {
        const name = input.name?.toLowerCase() || "";
        const id = input.id?.toLowerCase() || "";
        const type = input.type?.toLowerCase() || "";
        return (
          type === "password" ||
          sensitiveKeywords.some(keyword =>
            name.includes(keyword) || id.includes(keyword)
          )
        );
      });
      
      const isSafe = safeURLs.some(url => currentURL.startsWith(url));
      const alreadyInjected = document.getElementById("phishing-warning");
      
      if (hasSensitiveInput && !isSafe && !alreadyInjected) {
        const hostname = window.location.hostname.replace(/^www\./, '');
        
        // Get vote count using REST API
        getVoteCount(hostname).then(voteCount => {
          console.warn("⚠️ Potential phishing page detected:", currentURL);
          
          fetch(chrome.runtime.getURL("popup/warning.html"))
            .then(response => {
              if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
              }
              return response.text();
            })
            .then(html => {
              const warning = document.createElement('div');
              warning.id = "phishing-warning";
              warning.innerHTML = html;
              
              // Update message with vote count
              const messageElement = warning.querySelector("div:nth-child(2)");
              if (messageElement) {
                if (voteCount > 0) {
                  messageElement.innerHTML = `This site doesn't match any trusted login URLs.<br>However, <strong>${voteCount} user(s)</strong> have marked this site as safe.<br>Make sure you trust this page before entering any passwords.`;
                } else {
                  messageElement.innerHTML = `This site doesn't match any trusted login URLs.<br>No users have marked this site as safe yet.<br>Make sure you trust this page before entering any passwords.`;
                }
              }
              
              document.body.appendChild(warning);
              
              // Use setTimeout to ensure DOM is ready
              setTimeout(() => {
                const closeBtn = document.getElementById("close-warning");
                if (closeBtn) {
                  closeBtn.addEventListener("click", () => {
                    const popup = document.getElementById("phishing-warning");
                    if (popup) popup.remove();
                  });
                }

                const markBtn = document.getElementById("mark-safe");
                if (markBtn) {
                  markBtn.addEventListener("click", () => {
                    // Check if the user has already voted for this hostname
                    chrome.storage.local.get(['votedHosts'], (result) => {
                      if (chrome.runtime.lastError) {
                        console.error('Storage error:', chrome.runtime.lastError);
                        return;
                      }
                      
                      const votedHosts = result.votedHosts || [];
                      if (votedHosts.includes(hostname)) {
                        alert("You've already marked this site as safe.");
                        return;
                      }

                      // Proceed to vote using REST API
                      incrementVote(hostname).then(newCount => {
                        if (newCount !== null) {
                          console.log(`✅ Marked ${hostname} as safe (votes: ${newCount})`);
                          const updatedHosts = [...votedHosts, hostname];
                          chrome.storage.local.set({ votedHosts: updatedHosts }, () => {
                            if (chrome.runtime.lastError) {
                              console.error('Storage error:', chrome.runtime.lastError);
                            } else {
                              const popup = document.getElementById("phishing-warning");
                              if (popup) popup.remove();
                            }
                          });
                        } else {
                          alert("Failed to vote. Please try again.");
                        }
                      });
                    });
                  });
                }
              }, 100);
            })
            .catch(error => {
              console.error("Error loading warning popup:", error);
            });
        });
      }
    }

    // Run once on load
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', checkForPhishing);
    } else {
      checkForPhishing();
    }

    // Watch for future changes
    const observer = new MutationObserver(() => {
      checkForPhishing();
    });
    
    if (document.body) {
      observer.observe(document.body, { childList: true, subtree: true });
    }
  });
})();