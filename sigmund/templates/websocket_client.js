let socket;
let retryInterval;
const retryDelay = 5000;

function connectWebSocket() {
    try {
        socket = new WebSocket('ws://localhost:8080');
        
        socket.onopen = function () {
            console.log('Connected to server');
            if (retryInterval) {
                clearInterval(retryInterval); 
                retryInterval = null;
            }
            // CHANGED: Show the "connected-status" div on successful connection
            document.getElementById('connected-status').style.display = 'block';

            // Rebuild conversation history
            let action;
            let message;
			let workspace;
            socketSendMessage("clear_messages");
            for (let messageDiv of responseDiv.children) {
				workspace = messageDiv.querySelector('.message-workspace');
				if (workspace !== null) {
					workspace_content = messageDiv.querySelector('.workspace-content').textContent;
					workspace_language = messageDiv.querySelector('.workspace-language').textContent;
				} else {
					workspace_content = null;
					workspace_language = null;
				}
                messageDiv = copyAndStripDiv(messageDiv);
                if (messageDiv.classList.contains('message-ai')) {
                    action = 'ai_message';
                    message = messageDiv.getHTML();
                } else {
                    action = 'user_message';
                    message = messageDiv.textContent;
                }
                socketSendMessage(action, message, workspace_content, workspace_language, true);
            }
        };

        socket.onmessage = function (event) {
            try {
                const data = JSON.parse(event.data);
                if (data.action === 'user_message') {
                    messageInput.value = data.message;
                    setWorkspace(data.workspace_content, data.workspace_language);
                    sendMessage(data.message);
                }
            } catch (error) {
                // If the message does not adhere to the expected format, ignore it.
            }
        };

        socket.onclose = function () {
            console.log('Disconnected from server');
            document.getElementById('connected-status').style.display = 'none';
            startReconnect();
        };

        socket.onerror = function () {
            socket.close(); // Gracefully close socket on error
        };
    } catch (error) {
    }
}


function startReconnect() {
    if (!retryInterval) {
        retryInterval = setInterval(connectWebSocket, retryDelay); // Start retrying on disconnect
    }
}


function socketSendMessage(action, message, workspace_content, workspace_language, on_connect) {
	if (typeof on_connect === 'undefined') {
		on_connect = false;
	}
    const data = JSON.stringify({
        action: action,
        message: message,
        workspace_content: workspace_content,
        workspace_language: workspace_language,
		on_connect: on_connect
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
