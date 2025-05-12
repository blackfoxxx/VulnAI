// Store install commands
let installCommands = new Set();

// Helper function to show notifications
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    const notificationMessage = document.getElementById('notification-message');
    
    notification.className = `fixed bottom-4 right-4 transform transition-transform duration-300 ${
        type === 'success' ? 'bg-green-500' : 'bg-red-500'
    } text-white px-6 py-4 rounded-lg shadow-lg`;
    
    notificationMessage.textContent = message;
    notification.style.transform = 'translateY(0)';
    
    setTimeout(() => {
        notification.style.transform = 'translateY(100%)';
    }, 3000);
}

// Function to create a removable command
function createCommand(command, container, set) {
    const tag = document.createElement('div');
    tag.className = 'inline-flex items-center bg-gray-100 text-gray-800 rounded-full px-3 py-1 text-sm font-medium mr-2 mb-2';
    tag.innerHTML = `
        ${command}
        <button type="button" class="ml-2 text-gray-600 hover:text-gray-800 focus:outline-none">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    tag.querySelector('button').addEventListener('click', () => {
        set.delete(command);
        tag.remove();
    });
    
    container.appendChild(tag);
}

// Add install command
document.getElementById('add-command').addEventListener('click', () => {
    const input = document.getElementById('install-commands');
    const command = input.value.trim();
    
    if (command) {
        if (!installCommands.has(command)) {
            installCommands.add(command);
            createCommand(command, document.getElementById('commands-container'), installCommands);
            input.value = '';
        }
    }
});

// Load installed tools
async function loadTools() {
    try {
        const response = await fetch('/api/tools/list', {
            headers: {
                'X-Admin-Token': 'default_admin_token' // In production, use a secure token
            }
        });
        
        if (!response.ok) throw new Error('Failed to fetch tools');
        
        const data = await response.json();
        const container = document.getElementById('tools-list');
        container.innerHTML = '';
        
        Object.entries(data.tools).forEach(([name, info]) => {
            const toolDiv = document.createElement('div');
            toolDiv.className = 'py-4';
            toolDiv.innerHTML = `
                <div class="flex items-center justify-between">
                    <div>
                        <h3 class="text-lg font-medium text-gray-900">${name}</h3>
                        <p class="text-sm text-gray-500">${info.description || 'No description available'}</p>
                        <div class="mt-1">
                            ${info.category ? 
                                `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                    ${info.category}
                                </span>` : ''
                            }
                        </div>
                    </div>
                    <button onclick="removeTool('${name}')" class="text-red-600 hover:text-red-800">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
                <div class="mt-2 text-sm text-gray-600 space-y-1">
                    <div><span class="font-medium">Path:</span> ${info.path}</div>
                    <div><span class="font-medium">Virtual Env:</span> ${info.venv_path || 'None'}</div>
                    ${info.git_repo ? 
                        `<div><span class="font-medium">Repository:</span> 
                            <a href="${info.git_repo}" target="_blank" class="text-blue-600 hover:text-blue-800">
                                ${info.git_repo}
                            </a>
                        </div>` : ''
                    }
                </div>
            `;
            container.appendChild(toolDiv);
        });
    } catch (error) {
        console.error('Error loading tools:', error);
        showNotification('Failed to load installed tools', 'error');
    }
}

// Remove tool
async function removeTool(name) {
    if (!confirm(`Are you sure you want to remove ${name}?`)) return;
    
    try {
        const response = await fetch(`/api/tools/${name}`, {
            method: 'DELETE',
            headers: {
                'X-Admin-Token': 'default_admin_token' // In production, use a secure token
            }
        });
        
        if (!response.ok) throw new Error('Failed to remove tool');
        
        showNotification(`Tool ${name} removed successfully`);
        loadTools();
    } catch (error) {
        console.error('Error removing tool:', error);
        showNotification(`Failed to remove tool: ${error.message}`, 'error');
    }
}

// Load preconfigured tools
async function loadPreconfiguredTools() {
    try {
        const response = await fetch('/api/tools/preconfigured', {
            headers: {
                'X-Admin-Token': 'default_admin_token'
            }
        });
        
        if (!response.ok) throw new Error('Failed to fetch preconfigured tools');
        
        const data = await response.json();
        const container = document.getElementById('tool-name');
        
        // Add default empty option
        container.innerHTML = '<option value="">Select a tool or enter custom name</option>';
        
        // Add preconfigured tools
        Object.entries(data.tools).forEach(([name, info]) => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = `${info.name} - ${info.description}`;
            container.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading preconfigured tools:', error);
        showNotification('Failed to load preconfigured tools', 'error');
    }
}

// Handle tool selection
document.getElementById('tool-name').addEventListener('change', async (e) => {
    const toolName = e.target.value;
    if (!toolName) return;
    
    try {
        const response = await fetch('/api/tools/preconfigured', {
            headers: {
                'X-Admin-Token': 'default_admin_token'
            }
        });
        
        if (!response.ok) throw new Error('Failed to fetch tool info');
        
        const data = await response.json();
        const toolInfo = data.tools[toolName];
        
        if (toolInfo) {
            document.getElementById('git-repo').value = toolInfo.git_repo_url || '';
            installCommands.clear();
            document.getElementById('commands-container').innerHTML = '';
            
            toolInfo.install_commands.forEach(cmd => {
                installCommands.add(cmd);
                createCommand(cmd, document.getElementById('commands-container'), installCommands);
            });
        }
    } catch (error) {
        console.error('Error loading tool info:', error);
    }
});

// Form submission
document.getElementById('tool-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const toolName = document.getElementById('tool-name').value;
    const formData = {
        name: toolName,
        git_repo_url: document.getElementById('git-repo').value || null,
        install_commands: Array.from(installCommands),
        use_preconfigured: Boolean(toolName && !document.getElementById('git-repo').value)
    };
    
    try {
        const response = await fetch('/api/tools/install', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Admin-Token': 'default_admin_token' // In production, use a secure token
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) throw new Error('Failed to install tool');
        
        // Clear form
        e.target.reset();
        installCommands.clear();
        document.getElementById('commands-container').innerHTML = '';
        
        showNotification('Tool installed successfully');
        loadTools();
    } catch (error) {
        console.error('Error installing tool:', error);
        showNotification(`Failed to install tool: ${error.message}`, 'error');
    }
});

// Add keyboard shortcuts
document.getElementById('install-commands').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        document.getElementById('add-command').click();
    }
});

// Handle Register Tool Form Submission
document.getElementById('register-tool-form').addEventListener('submit', async (event) => {
    event.preventDefault();

    const toolName = document.getElementById('tool-name').value;
    const toolDescription = document.getElementById('tool-description').value;
    const toolCommand = document.getElementById('tool-command').value;
    const toolOutput = document.getElementById('tool-output').value;
    const toolGitRepo = document.getElementById('tool-git-repo').value;

    const payload = {
        name: toolName,
        description: toolDescription,
        command: toolCommand,
        expected_output: toolOutput,
        git_repo_url: toolGitRepo || null
    };

    try {
        const response = await fetch('/api/register-tool', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            const result = await response.json();
            showNotification(result.message, 'success');
            document.getElementById('register-tool-form').reset();
        } else {
            const error = await response.json();
            showNotification(error.detail, 'error');
        }
    } catch (error) {
        showNotification('Failed to register tool. Please try again.', 'error');
    }
});

// Initial load of installed tools
document.addEventListener('DOMContentLoaded', loadTools);
