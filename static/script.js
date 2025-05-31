document.addEventListener('DOMContentLoaded', () => {
    const fileUploadInput = document.getElementById('file-upload');
    const fileUploadArea = document.getElementById('upload-area');
    const fileList = document.getElementById('uploaded-files');
    const sendButton = document.getElementById('send-btn');
    const chatInput = document.getElementById('question-input');
    const chatMessages = document.getElementById('chat-messages');
    const container = document.querySelector('.container');
    const uploadBtn = document.getElementById('upload-btn');
    const refreshBtn = document.getElementById('refresh-btn');
    
    // Keep track of knowledge base status
    let knowledgeBaseReady = false;
    
    // Loader and toast elements are already in the HTML
    const loader = document.getElementById('loader');
    const toast = document.getElementById('toast');

    // Check if knowledge base is ready on page load
    checkKnowledgeBaseStatus();

    // DRAG & DROP SUPPORT
    fileUploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        fileUploadArea.style.borderColor = '#4361ee';
        fileUploadArea.style.backgroundColor = 'rgba(67, 97, 238, 0.05)';
    });

    fileUploadArea.addEventListener('dragleave', () => {
        fileUploadArea.style.borderColor = '#e0e0e0';
        fileUploadArea.style.backgroundColor = '';
    });

    fileUploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        fileUploadArea.style.borderColor = '#e0e0e0';
        fileUploadArea.style.backgroundColor = '';
        const files = e.dataTransfer.files;
        handleFiles(files);
    });

    // Add click event to the upload area itself
    fileUploadArea.addEventListener('click', () => {
        fileUploadInput.click();
    });

    // Add click event to the upload button
    uploadBtn.addEventListener('click', () => {
        fileUploadInput.click();
    });
    
    // Add click event to the refresh button
    refreshBtn.addEventListener('click', () => {
        checkKnowledgeBaseStatus();
    });

    fileUploadInput.addEventListener('change', () => {
        handleFiles(fileUploadInput.files);
        fileUploadInput.value = ''; // Allow re-upload of same file
    });

    function handleFiles(files) {
        const fileArray = Array.from(files);
        
        if (fileArray.length === 0) return;
        
        fileArray.forEach(file => {
            const fileName = file.name;
            const fileType = fileName.split('.').pop().toLowerCase();
            
            // Check file type
            const supportedTypes = ['pdf', 'docx', 'xlsx', 'csv', 'txt', 'md'];
            if (!supportedTypes.includes(fileType)) {
                showToast(`❌ Unsupported file type: ${fileType}`, 'error');
                return;
            }

            // Create file item in UI
            addFileToList(fileName, fileType);

            // Upload file to backend
            uploadFile(file);
        });
    }
    
    function addFileToList(fileName, fileType) {
        let icon = '📎';
        if (fileType === 'pdf') icon = '📄';
        else if (fileType === 'docx') icon = '📘';
        else if (fileType === 'xlsx') icon = '📊';
        else if (fileType === 'csv') icon = '📈';
        else if (fileType === 'txt' || fileType === 'md') icon = '📝';

        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.dataset.filename = fileName;
        fileItem.innerHTML = `
            <span class="file-icon">${icon}</span>
            <span class="file-name">${fileName}</span>
            <span class="processing-status status-processing">Processing...</span>
        `;

        fileList.appendChild(fileItem);
    }
    
    function updateFileStatus(fileName, status, message) {
        const fileItems = document.querySelectorAll('.file-item');
        
        for (const item of fileItems) {
            if (item.dataset.filename === fileName) {
                const statusElement = item.querySelector('.processing-status');
                
                if (status === 'done') {
                    statusElement.textContent = 'Processed';
                    statusElement.className = 'processing-status status-done';
                } else if (status === 'error') {
                    statusElement.textContent = 'Error';
                    statusElement.className = 'processing-status status-error';
                    statusElement.title = message;
                }
                
                break;
            }
        }
    }











    function uploadFile(file) {
        const fileName = file.name;
        const formData = new FormData();
        formData.append('file', file);
    
        // Show blur and loader
        container.classList.add('blur-effect');
        loader.classList.remove('hidden');
    
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(res => {
            console.log('Response status:', res.status);
            if (!res.ok) {
                return res.text().then(text => {
                    throw new Error(`Server returned ${res.status}: ${text}`);
                });
            }
            return res.json();
        })
        .then(data => {
            console.log('Success data:', data);
            updateFileStatus(fileName, 'done');
            showToast('✅ File processed successfully', 'success');
            knowledgeBaseReady = true;
            updateChatStatus();
        })
        .catch(err => {
            console.error('Fetch error:', err);
            updateFileStatus(fileName, 'error', err.message);
            showToast(`❌ Upload failed: ${err.message}`, 'error');
        })
        .finally(() => {
            container.classList.remove('blur-effect');
            loader.classList.add('hidden');
        });
    }










        






    // Show toast notification
    function showToast(message, type = 'success') {
        toast.textContent = message;
        toast.className = `toast ${type} visible`;

        setTimeout(() => {
            toast.className = `toast ${type} hidden`;
        }, 3000);
    }

    // CHAT FUNCTIONALITY
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;
        
        // Disable send button during processing
        sendButton.disabled = true;
        
        appendMessage('user', message);
        chatInput.value = '';

        // Show processing indicator
        appendMessage('system', 'Thinking...');
        
        fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question: message })
        })
        .then(response => response.json())
        .then(data => {
            // Remove the "Thinking..." message
            removeLastMessage();
            
            if (data.error) {
                appendMessage('bot', `Error: ${data.error}`);
            } else {
                appendMessage('bot', data.answer || "No answer received.");
            }
        })
        .catch(error => {
            // Remove the "Thinking..." message
            removeLastMessage();
            
            appendMessage('bot', "Error getting answer. Please try again later.");
            console.error('Error:', error);
        })
        .finally(() => {
            // Re-enable send button
            sendButton.disabled = false;
        });
    }

    function appendMessage(sender, text) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        
        if (sender === 'user') {
            messageDiv.classList.add('user-message');
        } else if (sender === 'bot') {
            messageDiv.classList.add('bot-message');
        } else if (sender === 'system') {
            messageDiv.classList.add('system-message');
        }
        
        messageDiv.innerText = text;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function removeLastMessage() {
        const messages = chatMessages.querySelectorAll('.message');
        if (messages.length > 0) {
            const lastMessage = messages[messages.length - 1];
            if (lastMessage.classList.contains('system-message')) {
                lastMessage.remove();
            }
        }
    }
    
    function checkKnowledgeBaseStatus() {
        // Show loading state
        sendButton.disabled = true;
        
        fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question: "system_check" })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error && data.error.includes("No knowledge base available")) {
                knowledgeBaseReady = false;
            } else {
                knowledgeBaseReady = true;
            }
        })
        .catch(error => {
            console.error('Error checking knowledge base:', error);
            knowledgeBaseReady = false;
        })
        .finally(() => {
            updateChatStatus();
        });
    }
    
    function updateChatStatus() {
        if (knowledgeBaseReady) {
            sendButton.disabled = false;
            chatInput.placeholder = "Type your question here...";
        } else {
            sendButton.disabled = true;
            chatInput.placeholder = "Upload documents first to enable chat...";
            
            // Check if we already have a notice message
            const messages = chatMessages.querySelectorAll('.message');
            let hasNotice = false;
            
            for (const msg of messages) {
                if (msg.textContent.includes("No knowledge base available")) {
                    hasNotice = true;
                    break;
                }
            }
            
            if (!hasNotice && messages.length <= 1) {
                appendMessage('system', "No knowledge base available. Please upload documents first.");
            }
        }
    }
});