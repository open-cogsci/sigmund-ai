let socket;
let retryInterval;
const retryDelay = 3000; // Retry every 3 seconds

function connectWebSocket() {
    try {
        socket = new WebSocket('ws://localhost:8080');
        
        socket.onopen = function () {
            console.log('Connected to server');
            if (retryInterval) {
                clearInterval(retryInterval); // Clear retry interval once connected
                retryInterval = null;
            }
        };

        socket.onmessage = function (event) {
            console.log('Received from server:', event.data);
            try {
                const data = JSON.parse(event.data);
                if (data.command === 'send_user_message') {
                    const { message, workspace_content, workspace_language } = data;

                    // Assuming these functions exist to handle the received data
                    messageInput.value = message;
                    setWorkspace(workspace_content, workspace_language);
                    sendMessage(message);
                }
            } catch (error) {
                // If the message does not adhere to the expected format, ignore it.
                console.error('Error parsing message data or data does not conform to expected format:', error);
            }
        };

        socket.onclose = function () {
            console.log('Disconnected from server');
            startReconnect();
        };

        socket.onerror = function () {
            console.log('Attempting to reconnect...');
            socket.close(); // Gracefully close socket on error
        };
    } catch (error) {
        console.log('Failed to connect:');
    }
}

function startReconnect() {
    if (!retryInterval) {
        retryInterval = setInterval(connectWebSocket, retryDelay); // Start retrying on disconnect
    }
}


function socketSendMessage(message, workspace_content, workspace_language) {
    const data = JSON.stringify({
        command: "send_ai_message",
        message: message,
        workspace_content: workspace_content,
        workspace_language: workspace_language,
    });
    console.log('Sending to server:', data);
    socket.send(data);
}


connectWebSocket(); // Initial attempt to connect
