// Global state
let availableTools = [];
let chatHistory = [];
let isProcessing = false;

// DOM Elements
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatContainer = document.getElementById('chat-container');
const toolsContainer = document.getElementById('tools-container');
const toolSearch = document.getElementById('tool-search');
const loadingOverlay = document.getElementById('loading-overlay');

// Show/Hide Loading
function showLoading(message = 'Loading...') {
    document.getElementById('loading-message').textContent = message;
    loadingOverlay.classList.remove('hidden');
    loadingOverlay.classList.add('flex');
}

function hideLoading() {
    loadingOverlay.classList.remove('flex');
    loadingOverlay.classList.add('hidden');
}

// Notification System
function showNotification(title, message, type = 'success') {
    const notificationEl = document.getElementById('notification');
    const titleEl = document.getElementById('notification-title');
    const messageEl = document.getElementById('notification-message');
    const iconEl = document.getElementById('notification-icon');
    
    titleEl.textContent = title;
    messageEl.textContent = message;
    
    // Set styles based on type
    const iconClass = type === 'success' ? 'fa-check-circle text-green-500' : 
                      type === 'error' ? 'fa-exclamation-circle text-red-500' : 
                      'fa-exclamation-triangle text-yellow-500';
    
    iconEl.className = `fas ${iconClass} text-xl`;
    
    // Show notification
    notificationEl.classList.remove('opacity-0', 'translate-y-full');
    notificationEl.classList.add('opacity-100', 'translate-y-0');
    
    // Auto-dismiss after 5 seconds
    setTimeout(dismissNotification, 5000);
}

function dismissNotification() {
    const notificationEl = document.getElementById('notification');
    notificationEl.classList.remove('opacity-100', 'translate-y-0');
    notificationEl.classList.add('opacity-0', 'translate-y-full');
}

// Fill chat input with example text
function fillChatInput(text) {
    chatInput.value = text;
    chatInput.focus();
}

// Add a message to the chat
function addMessage(sender, content, isToolOutput = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'flex items-start mb-4';
    
    // Avatar/icon
    const avatarDiv = document.createElement('div');
    avatarDiv.className = `w-8 h-8 rounded-full ${sender === 'You' ? 'bg-gray-600' : 'bg-blue-600'} flex items-center justify-center text-white mr-3 flex-shrink-0`;
    avatarDiv.innerHTML = `<i class="fas ${sender === 'You' ? 'fa-user' : 'fa-robot'}"></i>`;
    
    // Message content
    const contentDiv = document.createElement('div');
    contentDiv.className = `${sender === 'You' ? 'bg-gray-100' : 'bg-blue-50'} p-3 rounded-lg max-w-[85%]`;
    
    // Sender name
    const nameP = document.createElement('p');
    nameP.className = `font-medium ${sender === 'You' ? 'text-gray-900' : 'text-blue-900'}`;
    nameP.textContent = sender;
    
    // Message text
    const messageP = document.createElement('p');
    messageP.className = 'text-gray-700';
    
    if (isToolOutput) {
        // Create a pre element for tool output
        const pre = document.createElement('pre');
        pre.className = 'code-block text-xs mt-2 overflow-auto max-h-[400px]';
        pre.textContent = content;
        
        // Add a title for the tool output
        messageP.innerHTML = 'Tool Output:';
        contentDiv.appendChild(nameP);
        contentDiv.appendChild(messageP);
        contentDiv.appendChild(pre);
    } else {
        // Regular message
        messageP.innerHTML = content.replace(/\n/g, '<br>');
        contentDiv.appendChild(nameP);
        contentDiv.appendChild(messageP);
    }
    
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // Add to chat history
    chatHistory.push({
        sender: sender,
        content: content,
        isToolOutput: isToolOutput,
        timestamp: new Date().toISOString()
    });
}

// Show typing indicator
function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typing-indicator';
    typingDiv.className = 'flex items-start mb-4';
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white mr-3 flex-shrink-0';
    avatarDiv.innerHTML = '<i class="fas fa-robot"></i>';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'bg-blue-50 p-3 rounded-lg typing-indicator';
    contentDiv.innerHTML = '<span></span><span></span><span></span>';
    
    typingDiv.appendChild(avatarDiv);
    typingDiv.appendChild(contentDiv);
    
    chatContainer.appendChild(typingDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Remove typing indicator
function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Load available tools
async function loadTools() {
    try {
        const response = await fetch('/api/tools/list');
        const data = await response.json();
        availableTools = data.tools || [];
        renderTools();
    } catch (error) {
        console.error('Error loading tools:', error);
        showNotification('Error', 'Failed to load available tools', 'error');
        
        // Show placeholder tools in case of error
        availableTools = [
            {
                id: 'nmap',
                name: 'Nmap',
                description: 'Network scanner for discovering hosts and services',
                category: 'network',
                example: 'Run Nmap scan on 192.168.1.1'
            },
            {
                id: 'nuclei',
                name: 'Nuclei',
                description: 'Vulnerability scanner using templates',
                category: 'web_security',
                example: 'Scan example.com with Nuclei'
            },
            {
                id: 'whatweb',
                name: 'WhatWeb',
                description: 'Next generation web scanner',
                category: 'web_security',
                example: 'Check what technologies are used on example.com'
            }
        ];
        renderTools();
    }
}

// Render tools in the sidebar
function renderTools() {
    toolsContainer.innerHTML = '';
    
    if (availableTools.length === 0) {
        toolsContainer.innerHTML = '<p class="text-gray-500 text-center py-4">No tools available.</p>';
        return;
    }
    
    // Filter tools based on search
    const searchTerm = toolSearch.value.toLowerCase();
    const filteredTools = searchTerm ? 
        availableTools.filter(tool => 
            tool.name.toLowerCase().includes(searchTerm) || 
            tool.description.toLowerCase().includes(searchTerm)
        ) : 
        availableTools;
    
    // Group tools by category
    const categorizedTools = {};
    filteredTools.forEach(tool => {
        const category = tool.category || 'general';
        if (!categorizedTools[category]) {
            categorizedTools[category] = [];
        }
        categorizedTools[category].push(tool);
    });
    
    // Create tool cards by category
    Object.keys(categorizedTools).sort().forEach(category => {
        const categoryHeader = document.createElement('h3');
        categoryHeader.className = 'text-sm font-semibold text-gray-500 uppercase mt-4 mb-2';
        categoryHeader.textContent = category.replace('_', ' ');
        toolsContainer.appendChild(categoryHeader);
        
        categorizedTools[category].forEach(tool => {
            const toolCard = document.createElement('div');
            toolCard.className = 'tool-card bg-white border border-gray-200 rounded-lg p-4 mb-3 transition duration-300 hover:shadow-md';
            
            toolCard.innerHTML = `
                <h3 class="text-lg font-semibold text-blue-700">${tool.name}</h3>
                <p class="text-gray-600 text-sm mt-1">${tool.description}</p>
                <div class="mt-3 flex justify-between items-center">
                    <span class="text-xs text-gray-500">
                        <i class="fas fa-tag mr-1"></i> ${tool.category || 'General'}
                    </span>
                    <button class="text-blue-600 text-sm hover:text-blue-800 focus:outline-none" 
                        onclick="fillChatInput('${tool.example || `Run ${tool.name} on example.com`}')">
                        <i class="fas fa-play-circle mr-1"></i> Try
                    </button>
                </div>
            `;
            
            toolsContainer.appendChild(toolCard);
        });
    });
}

// Handle chat form submission
async function handleChatSubmission(event) {
    if (event) event.preventDefault();
    
    // Prevent multiple submissions
    if (isProcessing) return;
    
    const message = chatInput.value.trim();
    if (!message) return;
    
    // Check for tool addition requests
    const addToolPattern = /add(?:\sa|\sthe|\snew)?\s(?:tool|scanner|security\stool)(?:\scalled|\snamed)?\s([^\s,.]+)/i;
    const match = message.match(addToolPattern);
    
    if (match) {
        // Show the add tool form instead of sending the message directly
        const toolName = match[1];
        addMessage('You', message);
        chatInput.value = '';
        showAddToolForm(toolName);
        return;
    }
    
    // Add user message to chat
    addMessage('You', message);
    chatInput.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    isProcessing = true;
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator();
        isProcessing = false;
        
        if (data.tool_execution) {
            // Tool was executed
            addMessage('VulnLearnAI', `I'm executing the ${data.tool_execution.tool_name} tool for you...`);
            
            // Show tool output
            if (data.tool_execution.output) {
                addMessage('VulnLearnAI', data.tool_execution.output, true);
            }
            
            // Show AI analysis if available
            if (data.reply) {
                addMessage('VulnLearnAI', data.reply);
            }
        } else if (data.reply) {
            // Regular chat response
            addMessage('VulnLearnAI', data.reply);
        } else {
            addMessage('VulnLearnAI', 'I encountered an issue processing your request.');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        removeTypingIndicator();
        isProcessing = false;
        addMessage('VulnLearnAI', 'Sorry, I had trouble communicating with the server. Please try again.');
    }
}

// Show form for adding a new tool
function showAddToolForm(toolName = "") {
    const modalContainer = document.createElement('div');
    modalContainer.id = 'add-tool-modal';
    modalContainer.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center';
    
    const modalContent = document.createElement('div');
    modalContent.className = 'bg-white rounded-lg shadow-xl p-6 max-w-md w-full max-h-[90vh] overflow-y-auto';
    
    modalContent.innerHTML = `
        <h2 class="text-2xl font-semibold mb-4 flex items-center">
            <i class="fas fa-plus-circle text-blue-600 mr-3"></i>
            Add New Tool
        </h2>
        <form id="add-tool-form" class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Tool Name</label>
                <input type="text" id="tool-name" class="w-full border border-gray-300 rounded-lg px-4 py-2" 
                    placeholder="e.g., Nikto" value="${toolName}" required>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea id="tool-description" class="w-full border border-gray-300 rounded-lg px-4 py-2" 
                    placeholder="What does this tool do?" rows="2" required></textarea>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Command</label>
                <input type="text" id="tool-command" class="w-full border border-gray-300 rounded-lg px-4 py-2" 
                    placeholder="e.g., nikto -h {target}" required>
                <p class="text-xs text-gray-500 mt-1">Use {target}, {url}, or {domain} as placeholders for parameters</p>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Category</label>
                <select id="tool-category" class="w-full border border-gray-300 rounded-lg px-4 py-2">
                    <option value="web_security">Web Security</option>
                    <option value="network">Network</option>
                    <option value="forensics">Forensics</option>
                    <option value="recon">Reconnaissance</option>
                    <option value="custom">Custom</option>
                </select>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Expected Output</label>
                <textarea id="tool-output" class="w-full border border-gray-300 rounded-lg px-4 py-2" 
                    placeholder="What kind of output does this tool produce?" rows="2"></textarea>
            </div>
            <div class="flex justify-end space-x-3 pt-4 border-t border-gray-200">
                <button type="button" id="cancel-add-tool" class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded">
                    Cancel
                </button>
                <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                    <i class="fas fa-plus-circle mr-2"></i> Submit Tool
                </button>
            </div>
        </form>
    `;
    
    modalContainer.appendChild(modalContent);
    document.body.appendChild(modalContainer);
    
    // Focus on the first empty field
    if (!toolName) {
        document.getElementById('tool-name').focus();
    } else {
        document.getElementById('tool-description').focus();
    }
    
    // Handle form submission
    document.getElementById('add-tool-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const toolData = {
            name: document.getElementById('tool-name').value,
            description: document.getElementById('tool-description').value,
            command: document.getElementById('tool-command').value,
            category: document.getElementById('tool-category').value,
            expected_output: document.getElementById('tool-output').value
        };
        
        // Submit the tool addition request
        const message = `Add a new tool called ${toolData.name}. It's a ${toolData.description}. The command to run it is: ${toolData.command}. It belongs to the ${toolData.category} category. The expected output is: ${toolData.expected_output}.`;
        
        // Close the modal
        closeAddToolModal();
        
        // Add message to chat
        addMessage('You', message);
        
        // Show typing indicator
        showTypingIndicator();
        isProcessing = true;
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });
            
            const data = await response.json();
            
            // Remove typing indicator
            removeTypingIndicator();
            isProcessing = false;
            
            if (data.reply) {
                addMessage('VulnLearnAI', data.reply);
            } else {
                addMessage('VulnLearnAI', 'I encountered an issue processing your tool addition request.');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            removeTypingIndicator();
            isProcessing = false;
            addMessage('VulnLearnAI', 'Sorry, I had trouble communicating with the server. Please try again.');
        }
    });
    
    // Handle cancel button
    document.getElementById('cancel-add-tool').addEventListener('click', closeAddToolModal);
}

function closeAddToolModal() {
    const modal = document.getElementById('add-tool-modal');
    if (modal) {
        modal.remove();
    }
}

// Initialize the page
document.addEventListener('DOMContentLoaded', () => {
    // Load tools
    loadTools();
    
    // Handle form submission
    if (chatForm) {
        chatForm.addEventListener('submit', handleChatSubmission);
    }
    
    // Handle tool search
    if (toolSearch) {
        toolSearch.addEventListener('input', () => {
            renderTools();
        });
    }
    
    // Handle "Add Tool" button click
    const addToolBtn = document.getElementById('add-tool-btn');
    if (addToolBtn) {
        addToolBtn.addEventListener('click', () => {
            showAddToolForm();
        });
    }
    
    // Handle example commands clicks
    document.querySelectorAll('[onclick^="fillChatInput"]').forEach(el => {
        el.addEventListener('click', (e) => {
            const funcCall = el.getAttribute('onclick');
            if (funcCall) {
                const match = funcCall.match(/fillChatInput\('(.+?)'\)/);
                if (match && match[1]) {
                    fillChatInput(match[1]);
                }
            }
        });
    });
    
    // Add keyboard shortcut (Enter to send)
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleChatSubmission();
        }
    });
});
