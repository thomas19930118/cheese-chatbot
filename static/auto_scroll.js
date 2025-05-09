function scrollToBottom() {
    const messages = document.querySelector('.stChatMessageContainer');
    if (messages) {
        messages.scrollTop = messages.scrollHeight;
    }
}

// Create a MutationObserver to watch for new messages
const observer = new MutationObserver(() => {
    scrollToBottom();
});

// Start observing the chat container for changes
window.addEventListener('load', () => {
    const messages = document.querySelector('.stChatMessageContainer');
    if (messages) {
        observer.observe(messages, {
            childList: true,
            subtree: true
        });
        // Initial scroll to bottom
        scrollToBottom();
    }
}); 