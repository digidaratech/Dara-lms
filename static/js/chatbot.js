class Chatbot {
    constructor() {
        this.isOpen = false;
        this.messages = [];
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.addWelcomeMessage();
    }
    
    bindEvents() {
        const toggle = document.getElementById('chatbotToggle');
        const close = document.getElementById('chatbotClose');
        const send = document.getElementById('chatbotSend');
        const input = document.getElementById('chatbotInput');
        
        toggle.addEventListener('click', () => this.toggleChat());
        close.addEventListener('click', () => this.closeChat());
        send.addEventListener('click', () => this.sendMessage());
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }
    
    toggleChat() {
        const popup = document.getElementById('chatbotPopup');
        this.isOpen = !this.isOpen;
        
        if (this.isOpen) {
            popup.style.display = 'flex';
            document.getElementById('chatbotInput').focus();
        } else {
            popup.style.display = 'none';
        }
    }
    
    closeChat() {
        const popup = document.getElementById('chatbotPopup');
        popup.style.display = 'none';
        this.isOpen = false;
    }
    
    addWelcomeMessage() {
        // Welcome message is already in HTML
    }
    
    sendMessage() {
        const input = document.getElementById('chatbotInput');
        const message = input.value.trim();
        
        if (!message) return;
        
        // Add user message
        this.addMessage(message, 'user');
        input.value = '';
        
        // Show typing indicator
        this.showTyping();
        
        // Simulate API call (replace with actual API call)
        setTimeout(() => {
            this.hideTyping();
            this.getBotResponse(message);
        }, 1000);
    }
    
    addMessage(text, sender) {
        const messagesContainer = document.getElementById('chatbotMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message ${sender}-message`;
        
        if (sender === 'bot') {
            messageDiv.innerHTML = `<i class="fas fa-robot me-2"></i>${text}`;
        } else {
            messageDiv.innerHTML = `<i class="fas fa-user me-2"></i>${text}`;
        }
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    showTyping() {
        const messagesContainer = document.getElementById('chatbotMessages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chatbot-message bot-message typing-indicator';
        typingDiv.id = 'typingIndicator';
        typingDiv.innerHTML = '<i class="fas fa-robot me-2"></i>Typing...';
        
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    hideTyping() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    getBotResponse(userMessage) {
    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: userMessage })
    })
    .then(response => response.json())
    .then(data => {
        const botReply = data.response || "Sorry, I couldn't understand that.";
        this.addMessage(botReply, 'bot');
    })
    .catch(error => {
        console.error('Chatbot API error:', error);
        this.addMessage("Oops! Something went wrong. Please try again later.", 'bot');
    });
}
}
// Initialize chatbot when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new Chatbot();
});
