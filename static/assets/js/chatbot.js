// static/assets/js/chatbot.js (Modern & Interactive with /chatbot endpoint)

document.addEventListener('DOMContentLoaded', function() {
    const chatBtn = document.getElementById('chatBtn');
    const chatWindow = document.getElementById('chatWindow');
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');
    const chatMessages = document.getElementById('chatMessages');

    // 🔧 Force chat URL to use the correct backend route
    const chatUrl = "/chatbot";  // 👈 important: match Flask route

    // Toggle chat window
    chatBtn.addEventListener('click', () => {
        chatWindow.classList.toggle('open');
    });

    // Handle form submission
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const messageText = userInput.value.trim();
        if (messageText === '') return;

        appendMessage(messageText, 'user-message');
        userInput.value = '';

        // Show "typing" indicator
        showTypingIndicator();

        // Send message to Flask backend
        fetch(chatUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: messageText })
        })
        .then(response => response.json())
        .then(data => {
            removeTypingIndicator();
            appendMessage(data.response || "⚠️ No response received.", 'bot-message');
        })
        .catch(error => {
            console.error('Error contacting chatbot:', error);
            removeTypingIndicator();
            appendMessage('⚠️ Sorry, something went wrong. Please try again.', 'bot-message');
        });
    });

    // Add message to chat
    function appendMessage(html, type) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', type);
        messageDiv.innerHTML = html;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Show typing dots
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.classList.add('message', 'bot-message', 'bot-typing');
        typingDiv.innerHTML = `<span></span><span></span><span></span>`;
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Remove typing indicator
    function removeTypingIndicator() {
        const typingIndicator = chatMessages.querySelector('.bot-typing');
        if (typingIndicator) typingIndicator.remove();
    }
});
