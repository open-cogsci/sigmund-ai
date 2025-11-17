// Global variables for stream management
let currentEventSource = null;
let currentLoadingInterval = null;
let currentLoadingMessageBox = null;
let isStreaming = false;

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
    // If we're not logged in, this function is not defined.
    if (typeof connectWebSocket === 'function') {
        connectWebSocket();
    }
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

function showImageAttachments(message) {
    const imagePromises = [];
    attachments.forEach(file => {
        // Check if the file is an image based on MIME type
        if (file.type.startsWith('image/')) {
            // Create a promise to read the image as data URL
            const promise = new Promise((resolve) => {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const dataUrl = e.target.result;
                    const imgTag = `<div class="image-generation mask"><img src="${dataUrl}"></div>`;
                    resolve(imgTag);
                };
                reader.readAsDataURL(file);
            });
            imagePromises.push(promise);
        }
    });

    // Wait for all images to be processed and append them to the message
    Promise.all(imagePromises).then(imageTags => {
        for (i = 0; i < imageTags.length; i++) {
            const userMessageBox = document.createElement('div');
            userMessageBox.innerHTML = imageTags[i];
            userMessageBox.className = 'message-user message';
            userMessageBox.setAttribute('data-message-id', generateUUID());
            responseDiv.appendChild(userMessageBox);
        }
    });
}

function createWorkspaceDiv(content, language, messageId) {
    const workspaceDiv = document.createElement('div');
    workspaceDiv.className = 'message-workspace';
    workspaceDiv.id = 'message-workspace-' + messageId;

    const workspaceLoadLink = document.createElement('a');
    workspaceLoadLink.href = '#';
    workspaceLoadLink.innerHTML = 'Load workspace';
    workspaceLoadLink.onclick = () => {
        setWorkspace(content, language);
    };

    const workspaceContentPre = document.createElement('pre');
    workspaceContentPre.className = 'workspace-content';
    workspaceContentPre.textContent = content;

    const workspaceLanguageDiv = document.createElement('div');
    workspaceLanguageDiv.className = 'workspace-language';
    workspaceLanguageDiv.textContent = language;

    workspaceDiv.appendChild(workspaceLoadLink);
    workspaceDiv.appendChild(workspaceContentPre);
    workspaceDiv.appendChild(workspaceLanguageDiv);

    return workspaceDiv;
}

function createDeleteButton(messageId) {
    const deleteButton = document.createElement('button');
    deleteButton.className = 'message-delete';
    deleteButton.innerHTML = '<i class="fas fa-trash"></i>';
    deleteButton.onclick = () => deleteMessage(messageId);
    return deleteButton;
}

function displayUserMessage(message, messageId) {
    if (!message) return;

    const userMessageBox = document.createElement('div');
    userMessageBox.innerText = 'You: ' + message;
    userMessageBox.className = 'message-user message';
    userMessageBox.setAttribute('data-message-id', messageId);
    responseDiv.appendChild(userMessageBox);

    // Add delete button
    userMessageBox.prepend(createDeleteButton(messageId));

    // Add workspace if present
    const userWorkspaceContent = workspace.getValue();
    const userWorkspaceLanguage = workspace.getOption('mode');

    if (userWorkspaceContent) {
        const workspaceDiv = createWorkspaceDiv(userWorkspaceContent, userWorkspaceLanguage, messageId);
        userMessageBox.appendChild(workspaceDiv);
    }
}

function createLoadingIndicator() {
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

    const messageInterval = setInterval(updateMessage, 1000);

    return {
        element: loadingMessageBox,
        interval: messageInterval,
        setBaseMessage: (msg) => { baseMessage = msg; }
    };
}

function removeLoadingIndicator(loadingInfo) {
    if (loadingInfo.interval) {
        clearInterval(loadingInfo.interval);
    }
    if (loadingInfo.element && loadingInfo.element.parentNode) {
        loadingInfo.element.parentNode.removeChild(loadingInfo.element);
    }
}

function disableMessageInput() {
    messageInput.disabled = true;
    sendButton.disabled = true;
    sendButton.style.display = 'none';
    cancelButton.style.display = 'block';
}

function enableMessageInput() {
    messageInput.disabled = false;
    sendButton.style.display = 'block';
    cancelButton.style.display = 'none';
}

function prepareFormData(message, messageId, transient_settings, transient_system_prompt, foundation_document_topics) {
    const formData = new FormData();
    formData.append('message', message);
    formData.append('workspace_content', workspace.getValue());
    formData.append('workspace_language', workspace.getOption('mode'));
    formData.append('message_id', messageId);
    formData.append('transient_settings', transient_settings);
    formData.append('transient_system_prompt', transient_system_prompt);
    formData.append('foundation_document_topics', foundation_document_topics);

    // Append attached files
    attachments.forEach(file => {
        formData.append('attachments', file);
    });

    return formData;
}

function createAIMessageElement(data, metadata, forwardReplyToSocket) {
    const aiMessage = document.createElement('div');
    aiMessage.className = 'message-ai message';
    aiMessage.setAttribute('data-message-id', metadata['message_id']);
    aiMessage.innerHTML = data.response;

    // Add delete button
    aiMessage.prepend(createDeleteButton(metadata['message_id']));

    // Add workspace if present
    if (data.workspace_content !== null) {
        setWorkspace(data.workspace_content, data.workspace_language);
        const workspaceDiv = createWorkspaceDiv(data.workspace_content, data.workspace_language, metadata['message_id']);
        aiMessage.appendChild(workspaceDiv);
    }

    // Forward to socket if needed
    if (forwardReplyToSocket === true) {
        socketSendMessage("ai_message", data.response, data.workspace_content, data.workspace_language);
    }

    // Add timestamp
    const timestampDiv = document.createElement('div');
    timestampDiv.className = 'message-timestamp';
    timestampDiv.innerHTML = metadata['timestamp'];
    aiMessage.appendChild(timestampDiv);

    // Add answer model
    const answerModelDiv = document.createElement('div');
    answerModelDiv.className = 'message-answer-model';
    answerModelDiv.innerHTML = metadata['answer_model'];
    aiMessage.appendChild(answerModelDiv);

    // Add sources
    const sourcesDiv = document.createElement('div');
    const sources = JSON.parse(metadata.sources);
    sourcesDiv.className = 'message-sources';

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

    return aiMessage;
}

function displayErrorMessage() {
    const errorMessageBox = document.createElement('div');
    errorMessageBox.className = 'message-ai message message-error';
    errorMessageBox.setAttribute('data-message-id', generateUUID());

    let errorHTML = `<p>The connection to the server has been lost. This might be because:</p>
<ul>
    <li>Your login session has expired</li>
    <li>The server is temporarily unavailable</li>
    <li>There's a network connectivity issue</li>
</ul>
<p>Please reload the page to reconnect.</p>
<button onclick="location.reload()" class="modal-reload-button">Reload Page</button>
`;

    errorMessageBox.innerHTML = errorHTML;
    responseDiv.appendChild(errorMessageBox);
    errorMessageBox.scrollIntoViewIfNeeded();
}

function endStream() {
    clearAttachments();
    removeLoadingIndicator({
        element: currentLoadingMessageBox,
        interval: currentLoadingInterval
    });
    enableMessageInput();
    if (currentEventSource) {
        currentEventSource.close();
        currentEventSource = null;
    }
    isStreaming = false;
}

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
            endStream();
        }
    });
    cancelButton.onclick = null;
    cancelButton.style.display = 'none';
    socketSendMessage("cancel_message");
}

async function sendMessage(
        message,
        forwardReplyToSocket = false,
        transient_settings = null,
        transient_system_prompt = null,
        foundation_document_topics = null
) {
    console.log('user message: ' + message);
    setFavicon('static/loading.svg');
    isStreaming = true;
    const user_message_id = generateUUID();
    messageCounter.innerText = '';

    // Display user message
    displayUserMessage(message, user_message_id);
    showImageAttachments();

    // Show loading indicator
    const loadingInfo = createLoadingIndicator();
    currentLoadingMessageBox = loadingInfo.element;
    currentLoadingInterval = loadingInfo.interval;

    // Disable input
    disableMessageInput();
    chatAreaDiv.scrollTo(0, chatAreaDiv.scrollHeight);

    // Prepare and send initial request
    const formData = prepareFormData(message, user_message_id, transient_settings, transient_system_prompt, foundation_document_topics);

    try {
        await fetchWithRetry('{{ server_url }}/api/chat/start', {
            method: 'POST',
            body: formData
        });
    } catch (e) {
        console.error('Failed to start chat session:', e);
        isStreaming = false;
        return;
    }

    // Start streaming
    currentEventSource = new EventSource('{{ server_url }}/api/chat/stream');

    currentEventSource.onmessage = function(event) {
        console.log(event);
        const data = JSON.parse(event.data);

        // Handle actions
        if (typeof data.action !== 'undefined') {
            if (data.action == 'close') {
                endStream();
            } else if (data.action == 'set_loading_indicator') {
                loadingInfo.setBaseMessage(data.message);
            }
            return;
        }

        // Handle AI message
        const metadata = data.metadata;
        const aiMessage = createAIMessageElement(data, metadata, forwardReplyToSocket);

        // Append AI message after user message
        responseDiv.appendChild(aiMessage);
        aiMessage.scrollIntoViewIfNeeded();
        setFavicon(originalFavicon);
    };

    currentEventSource.onerror = function(event) {
        console.error('EventSource failed:', event);

        // Close the event source and clean up
        currentEventSource.close();
        removeLoadingIndicator(loadingInfo);
        enableMessageInput();
        setFavicon(originalFavicon);
        isStreaming = false;

        // Display a generic error message
        displayErrorMessage();
    };

    // Set up cancel button
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
    }).catch(error => console.error('Error deleting message:', error));
}

function requestBody(message, workspace_content, workspace_language, user_message_id) {
    return JSON.stringify({
        message: message,
        workspace_content: workspace_content,
        workspace_language: workspace_language,
        message_id: user_message_id
    });
}

function expandMessageBox() {
    document.getElementById('message-box').classList.toggle('expanded-message-box');
}

function setFavicon(url) {
    let faviconLink = document.querySelector('link[rel="icon"]');
    faviconLink.href = url;
}

document.addEventListener('DOMContentLoaded', globalElements);
document.addEventListener('DOMContentLoaded', initMain);