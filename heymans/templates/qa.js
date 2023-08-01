function initQA(event) {
    sendMessage('');
    
    restartButton.addEventListener('click', function() {
        window.location.href = '/qa';
    });
}

function requestBody(message, session_id) {
    return JSON.stringify({
        message: message, 
        session_id: sessionId
    })
}

const api_endpoint = 'api/qa'
window.addEventListener('load', initQA)
