function initWorkspace() {
    // Initialize CodeMirror workspace editor
    const workspaceTextArea = document.getElementById("workspace");
    let language = workspaceTextArea.getAttribute('data-mode') || 'markdown';
    workspace = CodeMirror.fromTextArea(workspaceTextArea, {
      lineNumbers: false,
      mode: language,
      theme: "monokai",
      tabSize: 4,
      lineWrapping: true
    })
    let mode = null;
    [language, mode] = workspaceLanguage(language);
    workspaceLanguageSelect.value = language;
    workspaceLanguageSelect.addEventListener("change", function() {
        const [language, mode] = workspaceLanguage(this.value);
        console.log('mode = ' + mode)
        workspace.setOption("mode", mode);
    });
    clearWorkspaceButton.addEventListener("click", function() {
        console.log('clearing workspace');
        workspace.setValue("");
    });
    copyWorkspaceButton.addEventListener("click", async function() {
        const content = workspace.getValue();
        try {
            await navigator.clipboard.writeText(content);
            console.log('Content successfully copied to clipboard');
        } catch (err) {
            console.error('Failed to copy to clipboard:', err);
        }
    });
    workspace.on('change', updateWorkspacePlaceholder);
    updateWorkspacePlaceholder();
};


function workspaceLanguage(language) {
    console.log(language);
    if (language === 'html') {
        return ['html', 'htmlmixed'];
    }
    if (language === 'opensesame') {
        return ['python', 'python'];
    }
    const languageExists = Array.from(workspaceLanguageSelect.options).some(option => option.value === language);
    if (!languageExists) {
        return ['markdown', 'markdown'];
    }
    return [language, language];
};

function setWorkspace(content, language) {
    let mode = null;
    [language, mode] = workspaceLanguage(language);
    workspace.setValue(content);
    workspace.setOption("mode", mode);
    workspaceLanguageSelect.value = language;
};


function loadMessageWorkspace(id) {
    const div = document.getElementById('message-workspace-' + id);
    const workspaceContent = div.querySelector('.workspace-content').innerText;
    const workspaceLanguage = div.querySelector('.workspace-language').innerText;
    setWorkspace(workspaceContent, workspaceLanguage);
};


function updateWorkspacePlaceholder() {
    if (workspace.getValue() === '') {
        workspacePlaceholder.style.display = 'block';
    } else {
        workspacePlaceholder.style.display = 'none';
    }
};
