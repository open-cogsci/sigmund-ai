function globalElements(event) {
    window.responseDiv = document.getElementById('response');
    window.loadingMessageDiv = document.getElementById('loading-message');
    window.documentationDiv = document.getElementById('documentation');
    window.courseInput = document.getElementById('course');
    window.chapterInput = document.getElementById('chapter');
    window.chatmodeInput = document.getElementById('chatmode');
    window.sendButton = document.getElementById('send');
    window.cancelButton = document.getElementById('cancel');
    window.messageInput = document.getElementById('message');
    window.messageCounter = document.getElementById('message-counter');
    window.messageBox = document.getElementById('message-box');
    window.chatArea = document.getElementById('chat-area');
    window.startInfo = document.getElementById('start-info');
    window.startButton = document.getElementById('start');
    window.courseGroup = document.getElementById("courseGroup");
    window.chapterGroup = document.getElementById("chapterGroup");
    window.exampleQueries = document.getElementById("example-queries");
    window.scrollTo(0, document.body.scrollHeight);
}

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
        // Enable the send button if there are at least 3 characters in the message box
        sendButton.disabled = this.value.length < 3;
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
    messageCounter.innerText = ''
    // Show the user's message
    if (message) {
        const userMessageBox = document.createElement('div');
        userMessageBox.innerText = 'You: ' + message;
        userMessageBox.className = 'message-user';
        responseDiv.appendChild(userMessageBox);
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
    window.scrollTo(0, document.body.scrollHeight);
    
    // Start the chat streaming. We need to do this through a separate endpoint
    // because the user message may be too long to fit into the URL that we use
    // for streaming.
    await fetchWithRetry('{{ server_url }}/api/chat/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: requestBody(message, searchFirst)
    }).catch(e => {
        console.error('Failed to start chat session:', e);
    });
    function endStream() {
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
        // Parse the JSON message data
        const data = JSON.parse(event.data);
        console.log(data)
        // If the message reflects an action, we process it separately.
        if (typeof data.action !== 'undefined') {
            if (data.action == 'close') {
                endStream();
            } else if (data.action == 'set_loading_indicator') {
                baseMessage = data.message;
            }
            return
        }
        // If the message is an actual message, we add it to the chat window
        // Create and append the message elements as in your existing code
        const aiMessage = document.createElement('div');
        aiMessage.className = 'message-ai';
        aiMessage.innerHTML = data.response;
        responseDiv.appendChild(aiMessage);
        // Parse the JSON string to an object
        const metadata = data.metadata
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
        sources.forEach(sourceObj => {
            if (sourceObj.url) {
                hasValidSources = true;
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
        window.scrollTo(0, document.body.scrollHeight);
    };

    eventSource.onerror = function(error) {
        console.error('EventSource failed:', error);
        eventSource.close(); // Close the connection on error
        loadingMessageDiv.removeChild(loadingMessageBox)
        clearInterval(messageInterval);
        messageInput.disabled = false; // Re-enable the message input
        responseDiv.innerText = 'Heymans: An error occurred, sorry! Please restart the conversation and try again.';
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
    }
    cancelButton.onclick = cancelStreaming;
}

function requestBody(message, searchFirst) {
    return JSON.stringify({message: message, search_first: searchFirst})
}

document.addEventListener('DOMContentLoaded', globalElements)
document.addEventListener('DOMContentLoaded', initMain)
