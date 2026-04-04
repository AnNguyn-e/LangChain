document.addEventListener('DOMContentLoaded', () => {
    // --- Elements ---
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const uploadStatus = document.getElementById('upload-status');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatBox = document.getElementById('chat-box');

    // --- File Upload Logic ---
    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('hover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('hover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('hover');
        if (e.dataTransfer.files.length) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFileUpload(e.target.files[0]);
        }
    });

    async function handleFileUpload(file) {
        if (!file.name.endsWith('.pdf') && !file.name.endsWith('.txt')) {
            showStatus('Chỉ hỗ trợ file PDF hoặc TXT.', 'error');
            return;
        }

        showStatus(`Đang upload ${file.name}...`, 'loading');
        
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                showStatus(`Thành công: ${data.message}`, 'success');
                setTimeout(() => showStatus('', ''), 3000);
            } else {
                showStatus(`Lỗi: ${data.detail}`, 'error');
            }
        } catch (error) {
            showStatus(`Upload thất bại: ${error.message}`, 'error');
        }
    }

    function showStatus(message, type) {
        uploadStatus.textContent = message;
        uploadStatus.className = 'status-message ' + (type ? `status-${type}` : '');
    }

    // --- Chat Logic ---
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const query = chatInput.value.trim();
        if (!query) return;

        // 1. Add User Message
        addMessage(query, 'user');
        chatInput.value = '';
        chatInput.style.height = 'auto'; // Reset height

        // 2. Add AI Typing Indicator
        const typingId = addTypingIndicator();

        // 3. Fetch AI Response
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });
            
            removeElement(typingId);

            if (!response.ok) {
                const err = await response.json();
                addMessage(`Lỗi: ${err.detail || 'Không thể kết nối tới server.'}`, 'ai', null, true);
                return;
            }

            const data = await response.json();
            addMessage(data.answer, 'ai', data.sources);
            
        } catch (error) {
            removeElement(typingId);
            addMessage(`Lỗi kết nối: ${error.message}`, 'ai', null, true);
        }
    });

    // --- Chat Utilities ---
    function addMessage(text, sender, sources = null, isError = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}-message`;
        
        let icon = sender === 'user' ? 'fa-user' : 'fa-robot';
        
        let formattedText = text.replace(/\n/g, '<br/>');
        formattedText = formattedText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        let sourceHtml = '';
        if (sources && sources.length > 0 && sources[0] !== 'Unknown') {
            sourceHtml = `<div class="sources">
                Nguồn tham khảo: ${sources.map(s => `<span class="source-tag">${s}</span>`).join('')}
            </div>`;
        }

        msgDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid ${icon}"></i></div>
            <div class="message-content" ${isError? 'style="color: var(--danger)"' : ''}>
                ${formattedText}
                ${sourceHtml}
            </div>
        `;
        
        chatBox.appendChild(msgDiv);
        scrollToBottom();
    }

    function addTypingIndicator() {
        const id = 'typing-' + Date.now();
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ai-message`;
        msgDiv.id = id;
        
        msgDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        
        chatBox.appendChild(msgDiv);
        scrollToBottom();
        return id;
    }

    function removeElement(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function scrollToBottom() {
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Auto-resize textarea
    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.scrollHeight > 150) {
            this.style.overflowY = 'auto';
        } else {
            this.style.overflowY = 'hidden';
        }
    });
});
