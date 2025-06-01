function initMain(event) {

    let maxLength = {{ max_message_length }};
    function updateCounter() {
        let length = messageInput.value.length;
        messageCounter.innerText = length + '/' + maxLength + ' characters';

        if (length >= maxLength) {
            messageInput.value = messageInput.value.slice(0, maxLength - 1);
        }
    }
    messageInput.addEventListener('input', updateCounter);
    updateCounter();
    
    messageInput.addEventListener('input', function() {
        // Enable the send button if there are at least 3 characters in the 
        // message box. This only happens when the need_login variable is not 
        // True.
        {% if not need_login %}
        sendButton.disabled = this.value.length < 3;
        {% endif %}
    });

    // Trigger the send button when Enter is pressed inside the message box
    messageInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            if (!sendButton.disabled) {
                sendButton.click();
            }
        }
    });
    
    sendButton.addEventListener('click', function() {
        // Send a message when the send button is clicked
        const message = messageInput.value;
        messageInput.value = '';
        sendMessage(message);
    });
    initWorkspace();
    connectWebSocket();
}

function generateUUID() {
    return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
        (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
    );
}

async function fetchWithRetry(url, options, retries = 3) {
    for (let i = 0; i < retries; i++) {
        try {
            return await fetch(url, options);
        } catch (err) {
            console.log('an error occurred while fetching: ' + err);
            if (i === retries - 1) throw err; // if last retry, throw error
        }
    }
}

async function sendMessage(message) {
    console.log('user message: ' + message)
    setFavicon('static/loading.svg');
    const user_message_id = generateUUID()
    messageCounter.innerText = ''
    // Show the user's message
    if (message) {
        const userMessageBox = document.createElement('div');
        userMessageBox.innerText = 'You: ' + message;
        userMessageBox.className = 'message-user message';
        userMessageBox.setAttribute('data-message-id', user_message_id);
        responseDiv.appendChild(userMessageBox);
        // Create a div for the delete button
        const deleteButton = document.createElement('button');
        deleteButton.className = 'message-delete';
        deleteButton.innerHTML = '<i class="fas fa-trash"></i>';
        deleteButton.onclick = () => deleteMessage(user_message_id);
        userMessageBox.prepend(deleteButton);
        // Retrieve user workspace content
        const userWorkspaceContent = workspace.getValue();
        const userWorkspaceLanguage = workspace.getOption('mode');
        // Create a workspace container if content is present
        if (userWorkspaceContent) {
            const userWorkspaceDiv = document.createElement('div');
            userWorkspaceDiv.className = 'message-workspace';
            userWorkspaceDiv.id = 'message-workspace-' + user_message_id;

            const workspaceLoadLink = document.createElement('a');
            workspaceLoadLink.href = '#';
            workspaceLoadLink.innerHTML = 'Load workspace';
            workspaceLoadLink.onclick = () => {
                // Load the user workspace content back into the editor
                setWorkspace(userWorkspaceContent, userWorkspaceLanguage);
            };

            const workspaceContentPre = document.createElement('pre');
            workspaceContentPre.className = 'workspace-content';
            workspaceContentPre.innerText = userWorkspaceContent;

            const workspaceLanguageDiv = document.createElement('div');
            workspaceLanguageDiv.className = 'workspace-language';
            workspaceLanguageDiv.innerText = userWorkspaceLanguage;

            userWorkspaceDiv.appendChild(workspaceLoadLink);
            userWorkspaceDiv.appendChild(workspaceContentPre);
            userWorkspaceDiv.appendChild(workspaceLanguageDiv);

            userMessageBox.appendChild(userWorkspaceDiv);
        }        
    }
    // Show the loading indicator and animate it
    const loadingMessageBox = document.createElement('div');
    let baseMessage = "{{ ai_name }} is reading your message ";
    loadingMessageBox.id = 'loading-message';
    loadingMessageBox.className = 'message-loading';
    loadingMessageBox.innerText = baseMessage;
    loadingMessageDiv.appendChild(loadingMessageBox);
    let dotCount = 0;
    function updateMessage() {
        dotCount = (dotCount % 3) + 1;
        let newMessage = baseMessage + '.'.repeat(dotCount);
        loadingMessageBox.innerText = newMessage;
    }
    let messageInterval = setInterval(updateMessage, 1000);
    // Disable the message input (will be reenabled when everything has been
    // received) and scroll down to the pge
    messageInput.disabled = true;
    sendButton.disabled = true;
    sendButton.style.display = 'none';
    cancelButton.style.display = 'block';
    chatAreaDiv.scrollTo(0, chatAreaDiv.scrollHeight);
    
    // Start the chat streaming. We need to do this through a separate endpoint
    // because the user message may be too long to fit into the URL that we use
    // for streaming.
    const formData = new FormData();

    // Append text fields
    formData.append('message', message);
    formData.append('workspace_content', workspace.getValue());
    formData.append('workspace_language', workspace.getOption('mode'));
    formData.append('message_id', user_message_id);

    // Append attached files
    attachments.forEach(file => {
        formData.append('attachments', file);
    });

    try {
        // Switch out JSON headers for a multipart/form-data request
        await fetchWithRetry('{{ server_url }}/api/chat/start', {
            method: 'POST',
            body: formData
        });
    } catch (e) {
        console.error('Failed to start chat session:', e);
    }
    function endStream() {
        clearAttachments();
        clearInterval(messageInterval);
        messageInput.disabled = false;
        sendButton.style.display = 'block';
        cancelButton.style.display = 'none';
        loadingMessageDiv.removeChild(loadingMessageBox);
        eventSource.close();    
    }
    // Now start streaming
    const eventSource = new EventSource('{{ server_url }}/api/chat/stream');
    eventSource.onmessage = function(event) {        
        console.log(event)
        // Parse the JSON message data
        const data = JSON.parse(event.data);
        // If the message reflects an action, we process it separately.
        if (typeof data.action !== 'undefined') {
            if (data.action == 'close') {
                endStream();
            } else if (data.action == 'set_loading_indicator') {
                baseMessage = data.message;
            }
            return
        }
        const metadata = data.metadata
        // If the message is an actual message, we add it to the chat window
        // Create and append the message elements as in your existing code
        const aiMessage = document.createElement('div');
        aiMessage.className = 'message-ai message';
        aiMessage.setAttribute('data-message-id', metadata['message_id']);
        aiMessage.innerHTML = data.response;
        responseDiv.appendChild(aiMessage);
        // Create a div for the delete button
        const deleteButton = document.createElement('button');
        deleteButton.className = 'message-delete';
        deleteButton.innerHTML = '<i class="fas fa-trash"></i>';
        deleteButton.onclick = () => deleteMessage(metadata['message_id']);
        aiMessage.prepend(deleteButton);
        // Update the workspace if any new information was given
        if (data.workspace_content !== null) {
            setWorkspace(data.workspace_content, data.workspace_language)
            const workspaceDiv = document.createElement('div');
            workspaceDiv.className = 'message-workspace';
            workspaceDiv.id = 'message-workspace-' + metadata['message_id'];
            const workspaceLoadLink = document.createElement('a');
            workspaceLoadLink.href = '#'
            workspaceLoadLink.innerHTML = 'Load workspace';
            workspaceLoadLink.onclick = () => loadMessageWorkspace(metadata['message_id'])
            workspaceContentPre = document.createElement('pre');
            workspaceContentPre.className = 'workspace-content';
            workspaceContentPre.innerHTML = data.workspace_content;
            workspaceLanguageDiv = document.createElement('div');
            workspaceLanguageDiv.className = 'workspace-language';
            workspaceLanguageDiv.innerText = data.workspace_language;
            workspaceDiv.appendChild(workspaceLoadLink);
            workspaceDiv.appendChild(workspaceContentPre);
            workspaceDiv.appendChild(workspaceLanguageDiv);
            aiMessage.appendChild(workspaceDiv);            
        }
        //
        socketSendMessage("ai_message", data.response, data.workspace_content, data.workspace_language);
        // Create a div for timestamp
        const timestampDiv = document.createElement('div');
        timestampDiv.className = 'message-timestamp';
        timestampDiv.innerHTML = metadata['timestamp'];
        aiMessage.appendChild(timestampDiv);
        // Create a div for timestamp
        const answerModelDiv = document.createElement('div');
        answerModelDiv.className = 'message-answer-model';
        answerModelDiv.innerHTML = metadata['answer_model'];
        aiMessage.appendChild(answerModelDiv);
        // Create a div for sources
        const sourcesDiv = document.createElement('div');
        const sources = JSON.parse(metadata.sources)
        sourcesDiv.className = 'message-sources';
        // Iterate over the sources and create clickable links for non-null sources
        // Flag to track if there are any valid sources
        // console.log(metadata['sources']);
        let hasValidSources = false;
        let uniqueURLs = new Set();
        
        sources.forEach(sourceObj => {
            if (sourceObj.url && !uniqueURLs.has(sourceObj.url)) {
                hasValidSources = true;
                uniqueURLs.add(sourceObj.url);
        
                const sourceLink = document.createElement('a');
                sourceLink.href = sourceObj.url;
                sourceLink.textContent = sourceObj.url;
                sourceLink.target = '_blank';
                sourcesDiv.appendChild(sourceLink);
                sourcesDiv.appendChild(document.createElement('br'));
            }
        });
        if (hasValidSources) {
            aiMessage.appendChild(sourcesDiv);
        }
        // Append the AI message div to the response div, just before the 
        // loading message.
        responseDiv.insertBefore(aiMessage, responseDiv.lastElementChild);
        aiMessage.scrollIntoViewIfNeeded();
        setFavicon(originalFavicon);
    };

    eventSource.onerror = function(error) {
        console.error('EventSource failed:', error);
        eventSource.close(); // Close the connection on error
        loadingMessageDiv.removeChild(loadingMessageBox)
        clearInterval(messageInterval);
        messageInput.disabled = false; // Re-enable the message input
        responseDiv.innerText = 'Sigmund: An error occurred, sorry! Please restart the conversation and try again.';
    };
    
    function cancelStreaming() {
        fetch('{{ server_url }}/api/chat/cancel', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ cancel: true })
        }).then(response => {
            if (response.ok) {
                console.log('Streaming cancelled by the client.');
                endStream()
            }
        });
        cancelButton.onclick = null;
        cancelButton.style.display = 'none';
        socketSendMessage("cancel_message");
    }
    cancelButton.onclick = cancelStreaming;
}

function deleteMessage(messageId) {
    fetch(`/api/message/delete/${messageId}`, {
        method: 'DELETE',
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const messageElement = document.querySelector(`.message[data-message-id="${messageId}"]`);
            if (messageElement) {
                messageElement.remove();
            }
        } else {
            console.error('Failed to delete message:', data.error);
        }
    }) .catch(error => console.error('Error deleting message:', error)); }



function requestBody(message, workspace_content, workspace_language, user_message_id) {
    return JSON.stringify({
        message: message,
        workspace_content: workspace_content,
        workspace_language: workspace_language,
        message_id: user_message_id
    })
}


function expandMessageBox() {
    document.getElementById('message-box').classList.toggle('expanded-message-box');
};


function setFavicon(url) {
    let faviconLink = document.querySelector('link[rel="icon"]');
    faviconLink.href = url;
};

document.addEventListener('DOMContentLoaded', globalElements)
document.addEventListener('DOMContentLoaded', initMain)
