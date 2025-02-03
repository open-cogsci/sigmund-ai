function globalElements(event) {
    window.responseDiv = document.getElementById('response');
    window.chatAreaDiv = document.getElementById('chat-area');
    window.loadingMessageDiv = document.getElementById('loading-message');
    window.sendButton = document.getElementById('send');
    window.cancelButton = document.getElementById('cancel');
    window.messageInput = document.getElementById('message');
    window.messageCounter = document.getElementById('message-counter');
    window.messageBox = document.getElementById('message-box');
    window.scrollTo(0, document.body.scrollHeight);
    window.workspaceLanguageSelect = document.getElementById('workspace-language');
    window.clearWorkspaceButton = document.getElementById('clear-workspace');
    window.copyWorkspaceButton = document.getElementById('copy-workspace');
    window.workspacePlaceholder = document.getElementById('workspace-placeholder');
    window.originalFavicon = document.querySelector('link[rel="icon"]').href;
}
