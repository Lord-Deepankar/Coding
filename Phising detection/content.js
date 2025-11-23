(function () {
  'use strict';

  // defined the database url itself 
  const databaseURL = "https://phishingguard-508b0-default-rtdb.firebaseio.com";

  const sensitiveKeywords = ["password", "username", "userid", "user id", "id", "aadhaar", "adhar", "user_name"];
  let lastCheckedURL = "";

  async function getVoteCount(hostname) {
    try {
      const sanitizedHostname = hostname.replace(/[.#$[\]]/g, '_');
      const response = await fetch(`${databaseURL}/userAddedUrls/${sanitizedHostname}.json`, { credentials: 'omit' });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return data || 0;
    } catch (error) {
      // Silent fail for production
      return 0;
    }
  }

  async function incrementVote(hostname) {
    try {
      const sanitizedHostname = hostname.replace(/[.#$[\]]/g, '_');
      let response = await fetch(`${databaseURL}/userAddedUrls/${sanitizedHostname}.json`, { credentials: 'omit' });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const currentCount = await response.json() || 0;
      const newCount = currentCount + 1;

      response = await fetch(`${databaseURL}/userAddedUrls/${sanitizedHostname}.json`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newCount),
        credentials: 'omit'
      });

      if (!response.ok) {
        const error = await response.text();
        if (response.status === 400 && error.includes('permission_denied')) {
          throw new Error('Vote rejected by security rules');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return newCount;
    } catch (error) {
      // Silent fail for production
      return null;
    }
  }

  async function isUrlInFirebaseSafeList(url) {
    try {
      const sanitizedFullUrlKey = url.replace(/[.#$[\]/]/g, '_');
      let response = await fetch(`${databaseURL}/safeUrls/${sanitizedFullUrlKey}.json`, { credentials: 'omit' });
      if ((await response.json()) !== null) return true;

      const hostname = new URL(url).hostname;

      const sanitizedHostnameKey = hostname.replace(/[.#$[\]]/g, '_');
      response = await fetch(`${databaseURL}/safeUrls/${sanitizedHostnameKey}.json`, { credentials: 'omit' });
      if ((await response.json()) !== null) return true;

      const domainParts = hostname.split('.');
      if (domainParts.length > 2) {
        const baseDomain = domainParts.slice(-2).join('.');
        const sanitizedBaseDomainKey = baseDomain.replace(/[.#$[\]]/g, '_');
        response = await fetch(`${databaseURL}/safeUrls/${sanitizedBaseDomainKey}.json`, { credentials: 'omit' });
        if ((await response.json()) !== null) return true;
      }

      return false;
    } catch (error) {
      // Silent fail for production
      return false;
    }
  }

  async function checkForPhishing() {
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
        sensitiveKeywords.some(keyword => name.includes(keyword) || id.includes(keyword))
      );
    });

    const isSafe = await isUrlInFirebaseSafeList(currentURL);
    const alreadyInjected = document.getElementById("phishing-warning");

    if (hasSensitiveInput && !isSafe && !alreadyInjected) {
      const hostname = window.location.hostname.replace(/^www\./, '');
      // getting the vote count from the database
      getVoteCount(hostname).then(voteCount => {
        fetch(chrome.runtime.getURL("popup/warning.html"))
          .then(response => response.text())
          .then(html => {
            const warning = document.createElement('div');
            warning.id = "phishing-warning";
            warning.innerHTML = html;

            const messageElement = warning.querySelector("div:nth-child(2)");
            if (messageElement) {
              if (voteCount > 0) {
                messageElement.innerHTML = `This site isn't on the trusted list.<br>However, <strong>${voteCount} user(s)</strong> have marked it as safe.<br>Please be certain before entering credentials.`;
              } else {
                messageElement.innerHTML = `This site isn't on the trusted list, and no users have marked it as safe.<br>We strongly advise you not to enter any passwords.`;
              }
            }

            document.body.appendChild(warning);

            setTimeout(() => {
              document.getElementById("close-warning")?.addEventListener("click", () => {
                document.getElementById("phishing-warning")?.remove();
              });

              document.getElementById("mark-safe")?.addEventListener("click", () => {
                chrome.storage.local.get(['votedHosts'], (result) => {
                  const votedHosts = result.votedHosts || [];
                  if (votedHosts.includes(hostname)) {
                    alert("You've already marked this site as safe.");
                    return;
                  }
                  incrementVote(hostname).then(newCount => {
                    if (newCount !== null) {
                      const updatedHosts = [...votedHosts, hostname];
                      chrome.storage.local.set({ votedHosts: updatedHosts }, () => {
                        document.getElementById("phishing-warning")?.remove();
                      });
                    } else {
                      alert("Failed to vote. Please try again.");
                    }
                  });
                });
              });
            }, 100);
          });
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', checkForPhishing);
  } else {
    checkForPhishing();
  }

  const observer = new MutationObserver(() => { checkForPhishing(); });
  if (document.body) {
    observer.observe(document.body, { childList: true, subtree: true });
  }

})();