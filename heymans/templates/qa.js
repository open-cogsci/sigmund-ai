function initQA(event) {
    restartButton.addEventListener('click', function() {
        window.location.href = '/qa';
    });
    var buttons = document.querySelectorAll('.example-query');
    buttons.forEach(function(button) {
        button.addEventListener('click', function() {
            sendMessage(this.innerText);
        });
    });
    sendMessage('');
}

function requestBody(message, session_id) {
    return JSON.stringify({
        message: message, 
        session_id: sessionId
    })
}

const api_endpoint = 'api/qa'
window.addEventListener('load', initQA)
