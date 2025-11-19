let healthCheckInterval = null;
let consecutiveFailures = 0;
const MAX_CONSECUTIVE_FAILURES = 3;
const GRACE_PERIOD_MS = 15000;

let lastVisibleTime = Date.now();

function showConnectionLostModal() {
    // Create modal if it doesn't exist
    let modal = document.getElementById('connection-lost-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'connection-lost-modal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <h2>Connection Lost</h2>
                <p>The connection to the server has been lost. This might be because:</p>
                <ul>
                    <li>Your login session has expired</li>
                    <li>The server is temporarily unavailable</li>
                    <li>There's a network connectivity issue</li>
                </ul>
                <p>Please reload the page to reconnect.</p>
                <button onclick="location.reload()" class="modal-reload-button">Reload Page</button>
            </div>
        `;
        document.body.appendChild(modal);
    }
    modal.style.display = 'flex';
}

function hideConnectionLostModal() {
    const modal = document.getElementById('connection-lost-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

async function checkHealth() {
    // Don't check during active streaming to avoid interruptions
    if (typeof isStreaming !== 'undefined' && isStreaming) {
        return;
    }

    // Grace period after tab becomes visible / device wakes
    const now = Date.now();
    if (now - lastVisibleTime < GRACE_PERIOD_MS) {
        return;
    }

    try {
        const response = await fetch('{{ server_url }}/api/health', {
            method: 'GET',
            cache: 'no-cache'
        });

        if (!response.ok) {
            console.error('Health check failed with status:', response.status);

            // Treat auth errors as "hard" failures (likely session timeout)
            if (response.status === 401 || response.status === 403) {
                showConnectionLostModal();
                // We don't stop the interval; user is expected to reload/login
                return;
            }

            consecutiveFailures += 1;
            if (consecutiveFailures >= MAX_CONSECUTIVE_FAILURES) {
                showConnectionLostModal();
            }
        } else {
            // Success: reset failure counter and hide modal if it was shown
            consecutiveFailures = 0;
            hideConnectionLostModal();
        }
    } catch (error) {
        console.error('Health check failed:', error);
        consecutiveFailures += 1;
        if (consecutiveFailures >= MAX_CONSECUTIVE_FAILURES) {
            showConnectionLostModal();
        }
    }
}

// Track visibility changes to detect "return" after sleep / tab backgrounding
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
        lastVisibleTime = Date.now();
        // On return, we also reset failures so we don't immediately show modal
        consecutiveFailures = 0;
    }
});

// Start periodic health checks
healthCheckInterval = setInterval(checkHealth, 60000);
checkHealth();