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
            // Rebuild the conversation history
            let action;
            let message;
            socketSendMessage("clear_messages");
            for (let messageDiv of responseDiv.children) {
                messageDiv = copyAndStripDiv(messageDiv);
                if (messageDiv.classList.contains('message-ai')) {
                    action = 'ai_message';
                    message = messageDiv.getHTML();
                } else {
                    action = 'user_message';
                    message = messageDiv.textContent;
                }
                socketSendMessage(action, message)
            }
        };

        socket.onmessage = function (event) {
            console.log('Received from server:', event.data);
            try {
                const data = JSON.parse(event.data);
                if (data.action === 'user_message') {
                    // Assuming these functions exist to handle the received data
                    messageInput.value = data.message;
                    setWorkspace(data.workspace_content, data.workspace_language);
                    sendMessage(data.message);
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


function socketSendMessage(action, message, workspace_content, workspace_language) {
    const data = JSON.stringify({
        action: action,
        message: message,
        workspace_content: workspace_content,
        workspace_language: workspace_language,
    });
    console.log('Sending to server:', data);
    socket.send(data);
}


function copyAndStripDiv(originalDiv) {
  // Clone the original div (deep clone, so copy all descendants)
  const clonedDiv = originalDiv.cloneNode(true);
  
  // List of classes to remove
  const classesToRemove = [
    'message-delete',
    'message-workspace',
    'message-sources',
    'message-timestamp',
    'message-answer-model'
  ];
  
  // For each class we want to remove
  for (const className of classesToRemove) {
    const elements = clonedDiv.querySelectorAll(`.${className}`);
    // Remove each matching element from the cloned div
    for (const el of elements) {
      el.remove();
    }
  }
  
  // Return the stripped clone
  return clonedDiv;
}
