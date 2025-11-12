let socket;
let retryInterval;
const retryDelay = 5000;
const maxMessages = 10;

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
            // Determine which messages to send (last maxMessages)
            const allMessages = Array.from(responseDiv.children || []);
            const total = allMessages.length;
            let messagesToSend = allMessages;
            if (total > maxMessages) {
                messagesToSend = allMessages.slice(total - maxMessages);
                // Send placeholder first
                socketSendMessage(
                    'ai_message',
                    `Only the last ${maxMessages} messages are shown. The full conversation history is available in the web interface.`,
                    null,
                    null,
                    true
                );
            }      
            
            for (let messageDiv of messagesToSend) {
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
                    // Process any attachments
                    if (data.attachments && data.attachments.length > 0) {
                        // Convert base64 to File objects
                        const files = data.attachments.map(att => {
                            // Decode base64 string to binary
                            const binary = atob(att.data);
                            const bytes = new Uint8Array(binary.length);
                            for (let i = 0; i < binary.length; i++) {
                                bytes[i] = binary.charCodeAt(i);
                            }
                            // Create Blob and File objects
                            const blob = new Blob([bytes], { type: att.mime_type });
                            return new File([blob], att.filename, { type: att.mime_type });
                        });
                        
                        // Add to global attachments array
                        if (typeof attachments !== 'undefined') {
                            attachments.push(...files);
                            // Update UI to show attachment count if updateAttachmentDisplay exists
                            if (typeof updateAttachmentDisplay === 'function') {
                                updateAttachmentDisplay();
                            }
                        }
                    }
                    
                    // Set message and workspace content
                    messageInput.value = data.message;
                    setWorkspace(data.workspace_content, data.workspace_language);
                    
                    // Send message (attachments will be included automatically)
                    // and indicate that the reply should be forwarded to the 
                    // socket.
                    sendMessage(
                        data.message,
                        true,
                        data.transient_settings,
                        data.transient_system_prompt,
                        data.foundation_document_topics
                    );
                    
                    // Clear message input after sending
                    messageInput.value = '';
                    
                    // Note: attachments should be cleared by sendMessage function
                    // after successfully sending the message
                    
                } else if (data.action === 'connector_name') {
                    const name = data.message;
                    document.getElementById('connected-status').innerHTML = ' Connected to ' + name;
                } else if (data.action === 'disable_code_execution') {
                    document.getElementById('tool-execute-code').checked = false;
                } else if (data.action === 'clear_conversation') {
                    window.location.href = '/api/conversation/clear';
                } else if (data.action === 'cancel_streaming') {
                    cancelStreaming();
                }
            } catch (error) {
                // If the message does not adhere to the expected format, ignore it.
                console.error('Error processing WebSocket message:', error);
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
