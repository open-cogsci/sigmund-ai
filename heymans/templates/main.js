function globalElements(event) {
    // Generate a unique session ID. This is not currently used because each
    // user has one continuous conversation.
    sessionId = 'session-' + Math.random().toString(36).substr(2, 9);
    window.responseDiv = document.getElementById('response');
    window.documentationDiv = document.getElementById('documentation');
    window.courseInput = document.getElementById('course');
    window.chapterInput = document.getElementById('chapter');
    window.chatmodeInput = document.getElementById('chatmode');
    window.sendButton = document.getElementById('send');
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
    if (message !== "" && exampleQueries !== null) {
        exampleQueries.style.display = 'none';
    }
    if (document.getElementById("user-message") !== null) {
        document.getElementById("user-message").style.display = 'none';
    }
    messageCounter.innerText = ''
    // Show the user's message
    if (message) {
        const userMessageBox = document.createElement('div');
        userMessageBox.innerText = 'You: ' + message;
        userMessageBox.className = 'message-user';
        responseDiv.appendChild(userMessageBox);
    }
    const loadingMessageBox = document.createElement('div');
    let baseMessage = "{{ ai_name }} is searching, thinking, and typing ";
    loadingMessageBox.id = 'loading-message';
    loadingMessageBox.className = 'message-loading';
    loadingMessageBox.innerText = baseMessage;
    responseDiv.appendChild(loadingMessageBox);
    let dotCount = 0;
    function updateMessage() {
        dotCount = (dotCount % 3) + 1;
        let newMessage = baseMessage + '.'.repeat(dotCount);
        loadingMessageBox.innerText = newMessage;
    }
    let messageInterval = setInterval(updateMessage, 1000);
    messageInput.disabled = true;
    sendButton.disabled = true;
    window.scrollTo(0, document.body.scrollHeight);

    let res;
    let data;
    try {
        res = await fetchWithRetry('{{ server_url }}/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: requestBody(message, sessionId)
        });
        console.log(res)
        data = await res.json();
        responseDiv.removeChild(loadingMessageBox)
    } catch (e) {
        responseDiv.innerText = 'Heymans: An error occurred, sorry! Please restart the conversation and try again.'
        console.log(e)
    }

    // Hide the loading indicator and enable the message box when a response is received
    clearInterval(messageInterval)
    messageInput.disabled = false;

    if (data.error) {
        responseDiv.innerText = 'Heymans: An error occurred, sorry! Please restart the conversation and try again.'
        console.log(data.error)
    } else {
        const aiMessage = document.createElement('div');
        aiMessage.className = 'message-ai';
        aiMessage.innerHTML = data.response;
        console.log('ai message: ' + data.response)
        if (data.response.includes('<FINISHED>') 
                || data.response.includes('<REPORTED>')
                || data.response.includes('<TOO_LONG>')) 
        {
            messageBox.style.display = 'none';
            messageCounter.style.display = 'none';
        }
        responseDiv.appendChild(aiMessage);
        if (data.response.includes('<FINISHED>')) {
            document.getElementsByTagName('body')[0].classList.add('body-finished');
        } else if (data.response.includes('<REPORTED>')) {
            document.getElementsByTagName('body')[0].classList.add('body-reported');
        }
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
        console.log(metadata['sources']);
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
        
        // Append the AI message div to the response div
        responseDiv.appendChild(aiMessage);
        window.scrollT(0, document.body.scrollHeight);
    }
}

function requestBody(message, session_id) {
    return JSON.stringify({
        message: message, 
        session_id: sessionId
    })
}

document.addEventListener('DOMContentLoaded', globalElements)
document.addEventListener('DOMContentLoaded', initMain)
