/**
 * Chatbot JavaScript functionality
 */

class Chatbot {
    constructor() {
        this.container = document.querySelector('.chatbot-container');
        this.toggle = document.querySelector('.chatbot-toggle');
        this.window = document.querySelector('.chatbot-window');
        this.closeBtn = document.querySelector('.chatbot-close');
        this.messagesContainer = document.querySelector('.chatbot-messages');
        this.input = document.querySelector('.chatbot-input');
        this.sendBtn = document.querySelector('.chatbot-send');

        this.isOpen = false;
        this.csrfToken = this.getCSRFToken();

        this.init();
    }

    init() {
        if (!this.container || !this.toggle || !this.window) return;

        // Toggle chatbot window
        if (this.toggle) {
            this.toggle.addEventListener('click', () => this.toggleWindow());
        }
        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => this.closeWindow());
        }

        // Send message on button click
        if (this.sendBtn) {
            this.sendBtn.addEventListener('click', () => this.sendMessage());
        }

        // Send message on Enter key
        if (this.input) {
            this.input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendMessage();
                }
            });
        }

        // Add welcome message
        if (this.messagesContainer) {
            this.addMessage('bot', '👋 Hello! I\'m your fundraising assistant. Here\'s what I can do:\n\n📧 Send email: "Send email to investor@email.com the draft of pitchdeck"\n\n🔍 Search: "Show me data for - \'keyword1\', \'keyword2\'"\n\nHow can I help you today?');
        }
    }

    getCSRFToken() {
        // Get CSRF token from cookie
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    toggleWindow() {
        this.isOpen = !this.isOpen;
        this.window.classList.toggle('active', this.isOpen);
        this.toggle.style.display = this.isOpen ? 'none' : 'flex';

        if (this.isOpen) {
            this.input.focus();
        }
    }

    closeWindow() {
        this.isOpen = false;
        this.window.classList.remove('active');
        this.toggle.style.display = 'flex';
    }

    addMessage(type, content) {
        const messageEl = document.createElement('div');
        messageEl.className = `chatbot-message ${type}`;
        messageEl.textContent = content;
        this.messagesContainer.appendChild(messageEl);
        this.scrollToBottom();
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    async sendMessage() {
        const message = this.input.value.trim();
        if (!message) return;

        // Add user message
        this.addMessage('user', message);
        this.input.value = '';

        // Show loading indicator
        const loadingEl = document.createElement('div');
        loadingEl.className = 'chatbot-message bot';
        loadingEl.textContent = '⏳ Thinking...';
        this.messagesContainer.appendChild(loadingEl);
        this.scrollToBottom();

        try {
            const response = await fetch('/api/chatbot/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({ message })
            });

            const data = await response.json();

            // Remove loading indicator
            loadingEl.remove();

            // Add bot response
            this.addMessage('bot', data.message);

        } catch (error) {
            loadingEl.remove();
            this.addMessage('bot', '❌ Sorry, something went wrong. Please try again.');
            console.error('Chatbot error:', error);
        }
    }
}

// Initialize chatbot when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new Chatbot();
});
