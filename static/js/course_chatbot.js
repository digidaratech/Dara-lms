class CourseAssistantChatbot {
    constructor(courseId, moduleId) {
        this.isOpen = false;
        this.messages = [];
        this.courseId = courseId;
        this.moduleId = moduleId;
        this.isTyping = false;
        this.init();
    }

    init() {
        this.bindEvents();
        this.addWelcomeMessage();
    }

    bindEvents() {
        const toggle = document.getElementById('courseChatbotToggle');
        const close = document.getElementById('courseChatbotClose');
        const send = document.getElementById('courseChatbotSend');
        const input = document.getElementById('courseChatbotInput');

        if (toggle) toggle.addEventListener('click', () => this.toggleChat());
        if (close) close.addEventListener('click', () => this.closeChat());
        if (send) send.addEventListener('click', () => this.sendMessage());

        if (input) {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendMessage();
                }
            });
        }
    }

    toggleChat() {
        const popup = document.getElementById('courseChatbotPopup');
        this.isOpen = !this.isOpen;

        if (this.isOpen) {
            popup.style.display = 'flex';
            const input = document.getElementById('courseChatbotInput');
            if (input) input.focus();
        } else {
            popup.style.display = 'none';
        }
    }

    closeChat() {
        const popup = document.getElementById('courseChatbotPopup');
        if (popup) {
            popup.style.display = 'none';
            this.isOpen = false;
        }
    }

    addWelcomeMessage() {}

    sendMessage() {
        const input = document.getElementById('courseChatbotInput');
        const message = input.value.trim();

        if (!message) return;

        this.addMessage(message, 'user');
        input.value = '';

        this.showTyping();

        setTimeout(() => {
            this.getCourseBotResponse(message);
        }, 600);
    }

    addMessage(text, sender) {
        const messagesContainer = document.getElementById('courseChatbotMessages');
        if (!messagesContainer) return;

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
        const messagesContainer = document.getElementById('courseChatbotMessages');
        if (!messagesContainer) return;

        const typingDiv = document.createElement('div');
        typingDiv.className = 'chatbot-message bot-message typing-indicator';
        typingDiv.id = 'courseTypingIndicator';
        typingDiv.innerHTML = '<i class="fas fa-robot me-2"></i><span id="typingDots">Thinking</span>';

        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        let dotCount = 0;
        this.typingInterval = setInterval(() => {
            dotCount = (dotCount + 1) % 4;
            document.getElementById('typingDots').innerText = 'Thinking' + '.'.repeat(dotCount);
        }, 300);
    }

    hideTyping() {
        clearInterval(this.typingInterval);
        const typingIndicator = document.getElementById('courseTypingIndicator');
        if (typingIndicator) typingIndicator.remove();
    }

    getCourseBotResponse(userMessage) {
        fetch('/course-assistant', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: userMessage,
                course_id: this.courseId,
                module_id: this.moduleId
            })
        })
        .then(response => {
            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('Please log in to use the Course Assistant.');
                } else if (response.status === 400) {
                    throw new Error('Course or module information missing. Please refresh the page and try again.');
                } else {
                    throw new Error('Server error. Try again in a moment.');
                }
            }
            return response.json();
        })
        .then(data => {
            this.hideTyping();

            let botReply = data.response || "Sorry, I couldn't understand that. Can you please rephrase your question?";
            this.simulateTypingEffect(botReply);
        })
        .catch(error => {
            console.error('Course Assistant API error:', error);
            this.hideTyping();
            this.addMessage(error.message || "Oops! Something went wrong. Please try again later.", 'bot');
        });
    }

    simulateTypingEffect(text) {
        const messagesContainer = document.getElementById('courseChatbotMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chatbot-message bot-message';
        messageDiv.innerHTML = `<i class="fas fa-robot me-2"></i>`;
        messagesContainer.appendChild(messageDiv);

        let i = 0;
        const interval = setInterval(() => {
            if (i < text.length) {
                messageDiv.innerHTML = `<i class="fas fa-robot me-2"></i>${text.substring(0, i + 1)}`;
                i++;
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            } else {
                clearInterval(interval);
            }
        }, 20);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.module-video-container');
    if (container) {
        const courseId = container.dataset.courseId;
        const moduleId = container.dataset.moduleId;

        if (courseId && moduleId) {
            new CourseAssistantChatbot(courseId, moduleId);
        }
    }
});
