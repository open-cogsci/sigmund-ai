// Allowed file extensions
const ALLOWED_EXTENSIONS = ['pdf', 'doc', 'docx', 'png', 'jpg'];
// Maximum file size in bytes (4 MB)
const MAX_FILE_SIZE = 4 * 1024 * 1024;

const attachmentInput = document.getElementById('attachment-input');
const attachmentList = document.getElementById('attachment-list');

// Store files in a global array if needed
let attachments = [];

// Listen for changes on the file input
attachmentInput.addEventListener('change', function(event) {
    const files = Array.from(event.target.files);

    // Clear the input, so if the user selects the same file again, we still trigger change
    attachmentInput.value = '';

    files.forEach(file => {
        validateAndAddFile(file);
    });
    
    renderAttachments();
});

// Listen for paste events for image content
window.addEventListener('paste', function(event) {
    const clipboardItems = (event.clipboardData || window.clipboardData).items;
    for (let item of clipboardItems) {
        if (item.kind === 'file') {
            const file = item.getAsFile();
            if (file) {
                // If it’s an image, guess the extension from the MIME type
                if (file.type.startsWith('image/')) {
                    let extension = file.type.split('/')[1].toLowerCase();
                    if (extension === 'jpeg') {
                        extension = 'jpg';
                    }
                    // Create a "File" with a guessed name if needed
                    // (some browsers might already provide file.name)
                    if (!file.name) {
                        file.name = `pasted_image.${extension}`;
                    }
                }

                validateAndAddFile(file);
            }
        }
    }
    renderAttachments();
});

function validateAndAddFile(file) {
    const extension = file.name.split('.').pop().toLowerCase();

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
        alert(`"${file.name}" is too large. The maximum allowed size is 4 MB.`);
    } else if (!ALLOWED_EXTENSIONS.includes(extension)) {
        alert(`"${file.name}" is not allowed. Allowed types are: ${ALLOWED_EXTENSIONS.join(', ')}.`);
    } else {
        // Add the file if valid
        attachments.push(file);
    }
}

function renderAttachments() {
    attachmentList.innerHTML = '';
    attachments.forEach((file, index) => {
        const attachmentItem = document.createElement('div');
        attachmentItem.style.margin = '5px 0';
        attachmentItem.classList.add('message-user');
        attachmentItem.classList.add('attachment-item');
        
        // Show file name
        const fileText = document.createElement('span');
        fileText.textContent = file.name;
        
        // Remove button
        const removeButton = document.createElement('button');
        removeButton.textContent = '✖';
        removeButton.style.marginLeft = '10px';
        removeButton.onclick = () => removeAttachment(index);

        attachmentItem.appendChild(fileText);
        attachmentItem.appendChild(removeButton);
        
        attachmentList.appendChild(attachmentItem);
    });
}

function removeAttachment(index) {
    attachments.splice(index, 1);
    renderAttachments();
}

function clearAttachments() {
    attachments = [];
    renderAttachments();
}

// Show menu on new discussion
if (document.getElementById('response').children.length < 2) {
    app.__vue__.toggleMenu()
}