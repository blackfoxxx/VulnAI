// Global state
let installCommands = new Set();
let categories = new Set();
let activeFilters = new Set();
let tools = {};

// DOM Elements
const loadingOverlay = document.getElementById('loading-overlay');
const notification = document.getElementById('notification');
const confirmModal = document.getElementById('confirm-modal');
const emptyState = document.getElementById('empty-state');
const toolsList = document.getElementById('tools-list');
const searchInput = document.getElementById('tool-search');
const categoryFilters = document.getElementById('category-filters');

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

    // Set notification style based on type
    const styles = {
        success: {
            bg: 'bg-green-100',
            text: 'text-green-800',
            icon: 'fa-check-circle text-green-500'
        },
        error: {
            bg: 'bg-red-100',
            text: 'text-red-800',
            icon: 'fa-exclamation-circle text-red-500'
        },
        warning: {
            bg: 'bg-yellow-100',
            text: 'text-yellow-800',
            icon: 'fa-exclamation-triangle text-yellow-500'
        }
    };

    const style = styles[type];
    notificationEl.querySelector('div').className = 
        `flex items-center space-x-4 p-4 rounded-lg shadow-lg max-w-md ${style.bg} ${style.text}`;
    iconEl.className = `fas ${style.icon} text-2xl`;
    
    titleEl.textContent = title;
    messageEl.textContent = message;
    
    notificationEl.style.transform = 'translateY(0)';
    
    setTimeout(() => hideNotification(), 5000);
}

function hideNotification() {
    notification.style.transform = 'translateY(100%)';
}

// Confirmation Modal
function showConfirmModal(title, message, onConfirm) {
    document.getElementById('confirm-title').textContent = title;
    document.getElementById('confirm-message').textContent = message;
    document.getElementById('confirm-action').onclick = () => {
        onConfirm();
        hideConfirmModal();
    };
    confirmModal.classList.remove('hidden');
    confirmModal.classList.add('flex');
}

function hideConfirmModal() {
    confirmModal.classList.remove('flex');
    confirmModal.classList.add('hidden');
}

// Command Management
function createCommand(command) {
    const tag = document.createElement('div');
    tag.className = 'inline-flex items-center bg-blue-50 text-blue-800 rounded-lg px-3 py-1 text-sm font-medium';
    tag.innerHTML = `
        <span class="mr-2">${command}</span>
        <button type="button" class="text-blue-600 hover:text-blue-800 focus:outline-none">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    tag.querySelector('button').addEventListener('click', () => {
        installCommands.delete(command);
        tag.remove();
    });
    
    document.getElementById('commands-container').appendChild(tag);
}

// Tool Card Creation
function createToolCard(name, info) {
    const card = document.createElement('div');
    card.className = 'bg-white rounded-xl shadow-lg p-6 transform transition-all duration-200 hover:shadow-xl hover:-translate-y-1';
    card.innerHTML = `
        <div class="flex justify-between items-start mb-4">
            <div>
                <h3 class="text-xl font-semibold text-gray-900">${name}</h3>
                ${info.category ? 
                    `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mt-2">
                        ${info.category}
                    </span>` : ''
                }
            </div>
            <button class="text-red-600 hover:text-red-800 transition-colors p-2" onclick="confirmRemoveTool('${name}')">
                <i class="fas fa-trash"></i>
            </button>
        </div>
        <p class="text-gray-600 text-sm mb-4">${info.description || 'No description available'}</p>
        <div class="space-y-2 text-sm text-gray-600">
            <div class="flex items-center">
                <i class="fas fa-folder-open w-5 text-gray-400"></i>
                <span class="ml-2">${info.path}</span>
            </div>
            ${info.venv_path ? `
                <div class="flex items-center">
                    <i class="fas fa-terminal w-5 text-gray-400"></i>
                    <span class="ml-2">${info.venv_path}</span>
                </div>
            ` : ''}
            ${info.git_repo ? `
                <div class="flex items-center">
                    <i class="fab fa-github w-5 text-gray-400"></i>
                    <a href="${info.git_repo}" target="_blank" 
                        class="ml-2 text-blue-600 hover:text-blue-800 truncate">
                        ${info.git_repo}
                    </a>
                </div>
            ` : ''}
        </div>
    `;
    return card;
}

// Category Filter Management
function createCategoryFilter(category) {
    const filter = document.createElement('button');
    filter.className = 'px-3 py-1 rounded-full text-sm font-medium transition-colors';
    filter.textContent = category;
    
    const updateStyle = () => {
        if (activeFilters.has(category)) {
            filter.className = 'px-3 py-1 rounded-full text-sm font-medium bg-blue-600 text-white';
        } else {
            filter.className = 'px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-600 hover:bg-gray-200';
        }
    };
    
    filter.onclick = () => {
        if (activeFilters.has(category)) {
            activeFilters.delete(category);
        } else {
            activeFilters.add(category);
        }
        updateStyle();
        filterTools();
    };
    
    updateStyle();
    return filter;
}

// Tool Filtering
function filterTools() {
    const searchTerm = searchInput.value.toLowerCase();
    const filteredTools = Object.entries(tools).filter(([name, info]) => {
        const matchesSearch = name.toLowerCase().includes(searchTerm) ||
            (info.description && info.description.toLowerCase().includes(searchTerm));
        const matchesCategory = activeFilters.size === 0 || 
            (info.category && activeFilters.has(info.category));
        return matchesSearch && matchesCategory;
    });

    toolsList.innerHTML = '';
    
    if (filteredTools.length === 0) {
        emptyState.classList.remove('hidden');
        toolsList.classList.add('hidden');
    } else {
        emptyState.classList.add('hidden');
        toolsList.classList.remove('hidden');
        filteredTools.forEach(([name, info]) => {
            toolsList.appendChild(createToolCard(name, info));
        });
    }
}

// Load Tools
async function loadTools() {
    try {
        showLoading('Loading installed tools...');
        const response = await fetch('/api/tools/list', {
            headers: {
                'X-Admin-Token': 'default_admin_token'
            }
        });
        
        if (!response.ok) throw new Error('Failed to fetch tools');
        
        const data = await response.json();
        tools = data.tools;
        
        // Extract categories
        categories.clear();
        Object.values(tools).forEach(info => {
            if (info.category) categories.add(info.category);
        });
        
        // Update category filters
        categoryFilters.innerHTML = '';
        categories.forEach(category => {
            categoryFilters.appendChild(createCategoryFilter(category));
        });
        
        filterTools();
    } catch (error) {
        console.error('Error loading tools:', error);
        showNotification(
            'Error Loading Tools',
            'Failed to load installed tools. Please try again.',
            'error'
        );
    } finally {
        hideLoading();
    }
}

// Remove Tool
function confirmRemoveTool(name) {
    showConfirmModal(
        'Remove Tool',
        `Are you sure you want to remove ${name}? This action cannot be undone.`,
        () => removeTool(name)
    );
}

async function removeTool(name) {
    try {
        showLoading(`Removing ${name}...`);
        const response = await fetch(`/api/tools/${name}`, {
            method: 'DELETE',
            headers: {
                'X-Admin-Token': 'default_admin_token'
            }
        });
        
        if (!response.ok) throw new Error('Failed to remove tool');
        
        showNotification(
            'Tool Removed',
            `${name} has been successfully removed.`,
            'success'
        );
        
        await loadTools();
    } catch (error) {
        console.error('Error removing tool:', error);
        showNotification(
            'Error Removing Tool',
            `Failed to remove ${name}: ${error.message}`,
            'error'
        );
    } finally {
        hideLoading();
    }
}

// Load Preconfigured Tools
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
        
        container.innerHTML = '<option value="">Select a tool or enter custom name</option>';
        
        Object.entries(data.tools).forEach(([name, info]) => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = `${info.name} - ${info.description}`;
            container.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading preconfigured tools:', error);
        showNotification(
            'Error Loading Tools',
            'Failed to load preconfigured tools. Please try again.',
            'error'
        );
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    loadTools();
    loadPreconfiguredTools();
    
    // Search input
    searchInput.addEventListener('input', filterTools);
    
    // Add command button
    document.getElementById('add-command').addEventListener('click', () => {
        const input = document.getElementById('install-commands');
        const command = input.value.trim();
        
        if (command && !installCommands.has(command)) {
            installCommands.add(command);
            createCommand(command);
            input.value = '';
        }
    });
    
    // Tool selection
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
                    createCommand(cmd);
                });
            }
        } catch (error) {
            console.error('Error loading tool info:', error);
            showNotification(
                'Error Loading Tool Info',
                'Failed to load tool information. Please try again.',
                'error'
            );
        }
    });
    
    // Form submission
    document.getElementById('tool-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const toolName = document.getElementById('tool-name').value;
        if (!toolName) {
            showNotification(
                'Validation Error',
                'Please select a tool or enter a custom name.',
                'error'
            );
            return;
        }
        
        const formData = {
            name: toolName,
            git_repo_url: document.getElementById('git-repo').value || null,
            install_commands: Array.from(installCommands),
            use_preconfigured: Boolean(toolName && !document.getElementById('git-repo').value)
        };
        
        try {
            showLoading('Installing tool...');
            const response = await fetch('/api/tools/install', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Admin-Token': 'default_admin_token'
                },
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) throw new Error('Failed to install tool');
            
            showNotification(
                'Tool Installed',
                `${toolName} has been successfully installed.`,
                'success'
            );
            
            // Clear form
            e.target.reset();
            installCommands.clear();
            document.getElementById('commands-container').innerHTML = '';
            
            await loadTools();
        } catch (error) {
            console.error('Error installing tool:', error);
            showNotification(
                'Error Installing Tool',
                `Failed to install ${toolName}: ${error.message}`,
                'error'
            );
        } finally {
            hideLoading();
        }
    });
    
    // Install commands keyboard shortcut
    document.getElementById('install-commands').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            document.getElementById('add-command').click();
        }
    });
});
