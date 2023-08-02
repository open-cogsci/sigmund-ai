function initPractice(event) {
    let courseContent = {{ course_content }};

    for (let course in courseContent) {
        let option = document.createElement('option');
        option.value = course;
        option.text = courseContent[course].title;
        courseInput.add(option);
    }

    function updatechapterInput(event) {
        while (chapterInput.firstChild) {
            chapterInput.firstChild.remove();
        }
        let selectedCourse = courseInput.value;
        let chapters = courseContent[selectedCourse].chapters;
        let option = document.createElement('option');
        option.value = '__any__';
        option.text = 'Any';
        chapterInput.add(option);
        for (let chapter in chapters) {
            option = document.createElement('option');
            option.value = chapter;
            option.text = chapters[chapter];
            chapterInput.add(option);
        }
    }
    updatechapterInput();
    courseInput.addEventListener('change', updatechapterInput);

    var params = new URLSearchParams(window.location.search);

    startButton.addEventListener('click', function() {
        if (chatmodeInput.value == 'practice') {
            startInfo.style.display = 'none';
            chatArea.style.display = 'block';
            sendMessage('');
        } else {
            window.location.href = '/qa';
        }
    });
    
    chatmodeInput.onchange = function() {
        if(chatmodeInput.value === "qa") {
            courseGroup.style.display = "none";
            chapterGroup.style.display = "none";
        } else {
            courseGroup.style.display = "block";
            chapterGroup.style.display = "block";
        }
    }
    
    restartButton.addEventListener('click', function() {
        window.location.href = '/practice';
    });
}

function requestBody(message, session_id) {
    return JSON.stringify({
        message: message, 
        session_id: sessionId,
        course: courseInput.value,
        chapter: chapterInput.value,
        chatmode: chatmodeInput.value
    })
}

const api_endpoint = 'api/practice'
document.addEventListener('DOMContentLoaded', initPractice)
