let sessionId = null;
let conversationFinished = false;

window.onload = function() {
    var params = new URLSearchParams(window.location.search);
    const nameInput =document.getElementById('name');
    if (params.has('name')) {
      nameInput.value = params.get('name');
    }
    const studentNrInput = document.getElementById('student_nr');
    if (params.has('student_nr')) {
      studentNrInput.value = params.get('student_nr');
    }
    // Generate a unique session ID
    sessionId = 'session-' + Math.random().toString(36).substr(2, 9);

    const sendButton = document.getElementById('send');
    const restartButton = document.getElementById('restart');
    const reportButton = document.getElementById('report');
    const messageInput = document.getElementById('message');
    const messageBox = document.getElementById('message-box');
    messageBox.style.display = 'none';
    const messageCounter = document.getElementById('message-counter');
    messageCounter.style.display = 'none';
    const controlBox = document.getElementById('control-box');
    controlBox.style.display = 'none';  // Hide the message box initially
    const responseDiv = document.getElementById('response');
    responseDiv.style.display = 'none';  // Hide the message box initially

    messageInput.addEventListener('input', function() {
        // Enable the send button if there are at least 3 characters in the message box
        sendButton.disabled = this.value.length < 3;
    });

    // Trigger the send button when Enter is pressed inside the message box
    messageInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            if (!sendButton.disabled) {
                sendButton.click();
            }
        }
    });

    document.getElementById('start').addEventListener('click', function() {
        this.style.display = 'none';  // Hide the start button
        document.getElementById('start-info').style.display = 'none';
        messageBox.style.display = 'flex'
        messageCounter.style.display = 'block'
        controlBox.style.display = 'block'
        responseDiv.style.display = 'block'
        sendMessage('');
    });

    sendButton.addEventListener('click', function() {
        // Send a message when the send button is clicked
        const message = messageInput.value;
        messageInput.value = '';
        if (!conversationFinished) {
            sendMessage(message);
        }
    });
    
    restartButton.addEventListener('click', function() {
        window.location.href = '/chat?name=' + nameInput.value + ' &student_nr=' + studentNrInput.value;
    });
    
    reportButton.addEventListener('click', function() {
        if (!conversationFinished) {
            sendMessage('<REPORT>');
        }
    });
};

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
    // Clear character counter
    const counter = document.getElementById('message-counter');
    counter.innerText = ''
    const responseDiv = document.getElementById('response');
    // Show the user's message
    if (message) {
        const userMessageBox = document.createElement('div');
        userMessageBox.innerText = 'You: ' + message;
        userMessageBox.className = 'message-user';
        responseDiv.appendChild(userMessageBox);
    }
    
    const loadingMessageBox = document.createElement('div');
    loadingMessageBox.id = 'loading-message';
    loadingMessageBox.innerText = '{{ ai_name }} is typing …';
    loadingMessageBox.className = 'message-loading';
    responseDiv.appendChild(loadingMessageBox);

    document.getElementById('message').disabled = true;
    document.getElementById('send').disabled = true;

    let res;
    let data;
    try {
        res = await fetchWithRetry('{{ server_url }}/api', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message, 
                session_id: sessionId,
                name: document.getElementById('name').value,
                student_nr: document.getElementById('student_nr').value,
                course: document.getElementById('course').value,
                chapter: document.getElementById('chapter').value
            })
        });
        data = await res.json();
    } catch (e) {
        responseDiv.innerText = 'Error: ' + e;
    }

    // Hide the loading indicator and enable the message box when a response is received
    responseDiv.removeChild(loadingMessageBox)
    document.getElementById('message').disabled = false;
    document.getElementById('restart').disabled = false;
    document.getElementById('report').disabled = false;

    if (data.error) {
        responseDiv.innerText = 'Error: ' + data.error;
    } else {
        const messageBox = document.createElement('div');
        messageBox.className = 'message-ai';
        messageBox.innerText = '{{ ai_name }}: ' + data.response;
        responseDiv.appendChild(messageBox);
        if (data.response.endsWith('<FINISHED>') || data.response.endsWith('<REPORTED>') ) {
            conversationFinished = true;
            document.getElementById('message-box').style.display = 'none';
            document.getElementById('message-counter').style.display = 'none';
            document.getElementById('report').style.display = 'none';
            document.getElementsByTagName('body')[0].classList.add('body-finished');
        }
    }
}

document.addEventListener('DOMContentLoaded', (event) => {
    let courseContent = {{ course_content }};
    let courseSelect = document.getElementById('course');
    let chapterSelect = document.getElementById('chapter');

    for (let course in courseContent) {
        let option = document.createElement('option');
        option.value = course;
        option.text = courseContent[course].title;
        courseSelect.add(option);
    }

    function updateChapterSelect() {
        // Clear existing options
        while (chapterSelect.firstChild) {
            chapterSelect.firstChild.remove();
        }

        let selectedCourse = courseSelect.value;
        let chapters = courseContent[selectedCourse].chapters;
        let option = document.createElement('option');
        option.value = '__any__';
        option.text = 'Any';
        chapterSelect.add(option);
        for (let chapter in chapters) {
            option = document.createElement('option');
            option.value = chapter;
            option.text = chapters[chapter];
            chapterSelect.add(option);
        }
    }

    // Call the function once at start to populate the chapter select
    updateChapterSelect();

    // Update the chapter select whenever the selected course changes
    courseSelect.addEventListener('change', updateChapterSelect);
    
    let textarea = document.getElementById('message');
    let maxLength = {{ max_message_length }};
    let counter = document.getElementById('message-counter');

    function updateCounter() {
        let length = textarea.value.length;
        counter.innerText = length + '/' + maxLength + ' characters';

        if (length >= maxLength) {
            textarea.value = textarea.value.slice(0, maxLength - 1);
        }
    }

    textarea.addEventListener('input', updateCounter);

    // Call the function once at start to initialize the counter
    updateCounter();
});
