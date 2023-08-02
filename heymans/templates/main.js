let sessionId = null;

function globalElements(event) {
    // Generate a unique session ID
    sessionId = 'session-' + Math.random().toString(36).substr(2, 9);
    window.responseDiv = document.getElementById('response');
    window.courseInput = document.getElementById('course');
    window.chapterInput = document.getElementById('chapter');
    window.chatmodeInput = document.getElementById('chatmode');
    window.sendButton = document.getElementById('send');
    window.restartButton = document.getElementById('restart');
    window.reportButton = document.getElementById('report');
    window.messageInput = document.getElementById('message');
    window.messageCounter = document.getElementById('message-counter');
    window.messageBox = document.getElementById('message-box');
    window.chatArea = document.getElementById('chat-area');
    window.startInfo = document.getElementById('start-info');
    window.startButton = document.getElementById('start');
    window.courseGroup = document.getElementById("courseGroup");
    window.chapterGroup = document.getElementById("chapterGroup");
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
    
    reportButton.addEventListener('click', function() {
        sendMessage('<REPORT>')
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

    let res;
    let data;
    try {
        res = await fetchWithRetry('{{ server_url }}/' + api_endpoint, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: requestBody(message, sessionId)
        });
        data = await res.json();
    } catch (e) {
        responseDiv.innerText = 'Error: ' + e;
    }

    // Hide the loading indicator and enable the message box when a response is received
    clearInterval(messageInterval)
    responseDiv.removeChild(loadingMessageBox)
    messageInput.disabled = false;
    restartButton.disabled = false;
    reportButton.disabled = false;

    if (data.error) {
        responseDiv.innerText = 'Error: ' + data.error;
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
            reportButton.style.display = 'none';
        }
        responseDiv.appendChild(aiMessage);
        if (data.response.includes('<FINISHED>')) {
            document.getElementsByTagName('body')[0].classList.add('body-finished');
        } else if (data.response.includes('<REPORTED>')) {
            document.getElementsByTagName('body')[0].classList.add('body-reported');
        }
    }
}

document.addEventListener('DOMContentLoaded', globalElements)
document.addEventListener('DOMContentLoaded', initMain)
