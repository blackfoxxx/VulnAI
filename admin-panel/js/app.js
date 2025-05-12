// Store links and CVEs
let writeupLinks = new Set();
let cveEntries = new Set();

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

// Function to create a removable tag
function createTag(value, container, set) {
    const tag = document.createElement('div');
    tag.className = 'inline-flex items-center bg-blue-100 text-blue-800 rounded-full px-3 py-1 text-sm font-medium mr-2 mb-2';
    tag.innerHTML = `
        ${value}
        <button type="button" class="ml-2 text-blue-600 hover:text-blue-800 focus:outline-none">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    tag.querySelector('button').addEventListener('click', () => {
        set.delete(value);
        tag.remove();
    });
    
    container.appendChild(tag);
}

// Add writeup link
document.getElementById('add-link').addEventListener('click', () => {
    const input = document.getElementById('writeup-links');
    const url = input.value.trim();
    
    if (url && url.startsWith('http')) {
        if (!writeupLinks.has(url)) {
            writeupLinks.add(url);
            createTag(url, document.getElementById('links-container'), writeupLinks);
            input.value = '';
        }
    } else {
        showNotification('Please enter a valid URL', 'error');
    }
});

// Add CVE
document.getElementById('add-cve').addEventListener('click', () => {
    const input = document.getElementById('cves');
    const cve = input.value.trim().toUpperCase();
    
    if (cve && /^CVE-\d{4}-\d{4,7}$/.test(cve)) {
        if (!cveEntries.has(cve)) {
            cveEntries.add(cve);
            createTag(cve, document.getElementById('cves-container'), cveEntries);
            input.value = '';
        }
    } else {
        showNotification('Please enter a valid CVE ID (e.g., CVE-2023-12345)', 'error');
    }
});

// Load recent entries
async function loadRecentEntries() {
    try {
        const response = await fetch('/api/admin/training-data', {
            headers: {
                'X-Admin-Token': 'default_admin_token' // In production, use a secure token
            }
        });
        
        if (!response.ok) throw new Error('Failed to fetch entries');
        
        const data = await response.json();
        const container = document.getElementById('recent-entries');
        container.innerHTML = '';
        
        data.entries.reverse().slice(0, 5).forEach(entry => {
            const entryDiv = document.createElement('div');
            entryDiv.className = 'border-l-4 border-blue-500 pl-4 mb-4';
            entryDiv.innerHTML = `
                <h3 class="text-lg font-semibold">${entry.title}</h3>
                <p class="text-gray-600 mt-1">${entry.description.substring(0, 150)}${entry.description.length > 150 ? '...' : ''}</p>
                <div class="mt-2">
                    ${entry.cves ? entry.cves.map(cve => 
                        `<span class="inline-block bg-red-100 text-red-800 text-xs px-2 py-1 rounded-full mr-2">${cve}</span>`
                    ).join('') : ''}
                </div>
                <div class="text-sm text-gray-500 mt-2">
                    Added on ${new Date(entry.timestamp).toLocaleDateString()}
                </div>
            `;
            container.appendChild(entryDiv);
        });
    } catch (error) {
        console.error('Error loading entries:', error);
        showNotification('Failed to load recent entries', 'error');
    }
}

// Form submission
document.getElementById('training-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = {
        title: document.getElementById('title').value,
        description: document.getElementById('description').value,
        writeup_links: Array.from(writeupLinks),
        cves: Array.from(cveEntries),
        metadata: {},
        timestamp: new Date().toISOString()
    };
    
    try {
        const response = await fetch('/api/admin/training-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Admin-Token': 'default_admin_token' // In production, use a secure token
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) throw new Error('Failed to submit data');
        
        // Clear form
        e.target.reset();
        writeupLinks.clear();
        cveEntries.clear();
        document.getElementById('links-container').innerHTML = '';
        document.getElementById('cves-container').innerHTML = '';
        
        showNotification('Training data submitted successfully');
        loadRecentEntries(); // Refresh the recent entries list
    } catch (error) {
        console.error('Error submitting form:', error);
        showNotification('Failed to submit training data', 'error');
    }
});

// Check model status and update UI
async function checkModelStatus() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        
        const statusElement = document.getElementById('model-status');
        if (data.components.ml_engine === 'operational') {
            statusElement.textContent = 'Model is trained and operational';
            statusElement.className = 'text-green-600';
        } else {
            statusElement.textContent = 'No trained model available';
            statusElement.className = 'text-yellow-600';
        }
    } catch (error) {
        console.error('Error checking model status:', error);
        const statusElement = document.getElementById('model-status');
        statusElement.textContent = 'Error checking model status';
        statusElement.className = 'text-red-600';
    }
}

// Train model
async function trainModel() {
    const trainButton = document.getElementById('train-model');
    const originalText = trainButton.innerHTML;
    
    try {
        trainButton.disabled = true;
        trainButton.innerHTML = `
            <i class="fas fa-spinner fa-spin mr-2"></i>
            Training...
        `;
        
        const response = await fetch('/api/train', {
            method: 'POST',
            headers: {
                'X-Admin-Token': 'default_admin_token' // In production, use a secure token
            }
        });
        
        if (!response.ok) throw new Error('Training failed');
        
        const result = await response.json();
        
        // Update training results
        document.getElementById('training-results').classList.remove('hidden');
        document.getElementById('validation-accuracy').textContent = 
            `${(result.validation_accuracy * 100).toFixed(1)}%`;
        document.getElementById('training-samples').textContent = 
            result.training_samples;
        document.getElementById('training-timestamp').textContent = 
            new Date(result.timestamp).toLocaleString();
        
        showNotification('Model trained successfully');
        checkModelStatus();
    } catch (error) {
        console.error('Error training model:', error);
        showNotification('Failed to train model', 'error');
    } finally {
        trainButton.disabled = false;
        trainButton.innerHTML = originalText;
    }
}

// Event listener for train model button
document.getElementById('train-model').addEventListener('click', trainModel);

// Initial load
document.addEventListener('DOMContentLoaded', () => {
    loadRecentEntries();
    checkModelStatus();
});

// Add keyboard shortcuts for adding links and CVEs
document.getElementById('writeup-links').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        document.getElementById('add-link').click();
    }
});

document.getElementById('cves').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        document.getElementById('add-cve').click();
    }
});

// Handle Tool Execution Form Submission
document.getElementById('tool-execution-form').addEventListener('submit', async (event) => {
  event.preventDefault();

  const toolName = document.getElementById('tool-name').value;
  const toolParameters = document.getElementById('tool-parameters').value;

  try {
    const response = await fetch('/api/chat/tool', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        tool_name: toolName,
        parameters: JSON.parse(toolParameters)
      })
    });

    const outputDiv = document.getElementById('tool-output');
    const outputPre = outputDiv.querySelector('pre');

    if (response.ok) {
      const result = await response.json();
      outputPre.textContent = result.output;
      outputDiv.classList.remove('hidden');
    } else {
      const error = await response.json();
      outputPre.textContent = `Error: ${error.detail}`;
      outputDiv.classList.remove('hidden');
    }
  } catch (error) {
    const outputDiv = document.getElementById('tool-output');
    const outputPre = outputDiv.querySelector('pre');
    outputPre.textContent = 'Failed to execute tool. Please try again.';
    outputDiv.classList.remove('hidden');
  }
});
