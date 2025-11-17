function showConnectionLostModal() {
    // Create modal if it doesn't exist
    let modal = document.getElementById('connection-lost-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'connection-lost-modal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <h2>🔌 Connection Lost</h2>
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

async function checkHealth() {
    // Don't check during active streaming to avoid interruptions
    if (isStreaming) {
        return;
    }

    try {
        const response = await fetch('{{ server_url }}/api/health', {
            method: 'GET',
            cache: 'no-cache'
        });

        if (!response.ok) {
            console.error('Health check failed with status:', response.status);
            showConnectionLostModal();
            stopHealthCheck();
        }
    } catch (error) {
        console.error('Health check failed:', error);
        showConnectionLostModal();
        stopHealthCheck();
    }
}

function stopHealthCheck() {
    if (healthCheckInterval) {
        clearInterval(healthCheckInterval);
        healthCheckInterval = null;
    }
}


let healthCheckInterval = setInterval(checkHealth, 60000);
checkHealth();
