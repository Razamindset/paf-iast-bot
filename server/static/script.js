const chatWindow = document.getElementById('chat-window');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

function appendMessage(text, isBot = true) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${isBot ? 'bot-message' : 'user-message'}`;
    
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Parse markdown for both bot and user (bot uses it most)
    const contentHtml = marked.parse(text);
    
    msgDiv.innerHTML = `
        <div class="message-content">${contentHtml}</div>
        <div class="message-time">${time}</div>
    `;
    
    chatWindow.appendChild(msgDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function handleSendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    // Append user message
    appendMessage(text, false);
    userInput.value = '';

    // Show typing indicator
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'typing';
    typingIndicator.innerText = 'PAF-IAST Bot is thinking...';
    chatWindow.appendChild(typingIndicator);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: text })
        });

        const data = await response.json();
        
        // Remove typing indicator
        chatWindow.removeChild(typingIndicator);

        if (data.answer) {
            appendMessage(data.answer, true);
        } else if (data.detail) {
            appendMessage("Error: " + data.detail, true);
        }
    } catch (error) {
        chatWindow.removeChild(typingIndicator);
        appendMessage("Sorry, I'm having trouble connecting to the server. Please try again later.", true);
        console.error(error);
    }
}

sendBtn.addEventListener('click', handleSendMessage);

userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleSendMessage();
    }
});
