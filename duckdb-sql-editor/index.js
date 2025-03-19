// Line number functionality
function updateLineNumbers() {
    const editor = document.getElementById('sql-query');
    const lineNumbers = document.getElementById('line-numbers');
    if (!editor || !lineNumbers) return;
    
    const lines = editor.value.split('\\n');
    let lineNumbersText = '';
    
    for (let i = 1; i <= lines.length; i++) {
        lineNumbersText += i + '\\n';
    }
    
    lineNumbers.textContent = lineNumbersText;
    
    // Ensure line numbers have the same height as the editor content
    lineNumbers.style.height = editor.scrollHeight + 'px';
}

// Enhanced table schema toggle
function toggleSchema(tableId) {
    console.log('Toggling schema for table:', tableId);
    const schemaContainer = document.getElementById(`schema-${tableId}`);
    const tableHeader = document.getElementById(`table-header-${tableId}`);
    const toggleIndicator = document.getElementById(`toggle-${tableId}`);
    
    if (!schemaContainer || !tableHeader) {
        console.error('Schema container or table header not found');
        return;
    }
    
    // Toggle active class and open state
    const isOpen = tableHeader.classList.contains('active');
    
    // Close all schemas first
    document.querySelectorAll('.schema-container').forEach(container => {
        container.classList.remove('open');
    });
    document.querySelectorAll('.table-header').forEach(header => {
        header.classList.remove('active');
    });
    document.querySelectorAll('.toggle-indicator').forEach(indicator => {
        indicator.classList.remove('open');
    });
    
    // Toggle this schema if it wasn't the one that was open
    if (!isOpen) {
        tableHeader.classList.add('active');
        schemaContainer.classList.add('open');
        toggleIndicator.classList.add('open');
        console.log(`Opening schema for ${tableId}`);
    } else {
        console.log(`Closing schema for ${tableId}`);
    }
}

// Format JSON for display
function formatJsonForDisplay(jsonString, indent = 2) {
    try {
        const parsedJson = JSON.parse(jsonString);
        return JSON.stringify(parsedJson, null, indent);
    } catch (e) {
        console.error('Error formatting JSON:', e);
        return jsonString;
    }
}

// Toggle JSON prettification
function toggleJsonPrettify(element) {
    const jsonCell = element.closest('.json-cell');
    const jsonData = jsonCell.getAttribute('data-json');
    const prettifiedContainer = jsonCell.querySelector('.json-prettified');
    
    if (prettifiedContainer.style.display === 'none' || !prettifiedContainer.style.display) {
        prettifiedContainer.textContent = formatJsonForDisplay(jsonData);
        prettifiedContainer.style.display = 'block';
    } else {
        prettifiedContainer.style.display = 'none';
    }
}

// Open JSON explorer modal
function openJsonExplorer(jsonString, columnName) {
    try {
        // Parse the JSON
        const jsonData = JSON.parse(jsonString);
        
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'json-explorer-modal';
        modal.id = 'json-explorer-modal';
        
        // Create modal content
        modal.innerHTML = `
            <div class="json-explorer-content">
                <div class="json-explorer-header">
                    <h3 class="text-lg font-semibold">JSON Explorer: ${columnName}</h3>
                    <button class="close-modal-btn" onclick="closeJsonExplorer()">×</button>
                </div>
                <div class="json-path" id="current-json-path">$</div>
                <div class="json-explorer-body">
                    <div class="json-tree" id="json-tree"></div>
                    <div class="json-content" id="json-content">${formatJsonForDisplay(jsonString)}</div>
                </div>
            </div>
        `;
        
        // Add to document
        document.body.appendChild(modal);
        
        // Generate tree
        generateJsonTree(jsonData, document.getElementById('json-tree'), '$');
        
    } catch (e) {
        console.error('Error opening JSON explorer:', e);
        alert('Error parsing JSON data');
    }
}

// Close JSON explorer modal
function closeJsonExplorer() {
    const modal = document.getElementById('json-explorer-modal');
    if (modal) {
        document.body.removeChild(modal);
    }
}

// Generate JSON tree
function generateJsonTree(data, container, path = '$') {
    if (Array.isArray(data)) {
        // Handle array
        const list = document.createElement('div');
        list.className = 'json-tree-children';
        
        for (let i = 0; i < data.length; i++) {
            const itemPath = `${path}[${i}]`;
            const item = document.createElement('div');
            item.className = 'json-tree-item';
            
            const valueType = typeof data[i];
            const isComplex = valueType === 'object' && data[i] !== null;
            
            if (isComplex) {
                const toggle = document.createElement('span');
                toggle.className = 'json-tree-toggle';
                toggle.textContent = '▶';
                toggle.onclick = function(e) {
                    e.stopPropagation();
                    const childContainer = this.parentNode.querySelector('.json-tree-children');
                    if (childContainer.style.display === 'none') {
                        childContainer.style.display = 'block';
                        this.textContent = '▼';
                    } else {
                        childContainer.style.display = 'none';
                        this.textContent = '▶';
                    }
                };
                item.appendChild(toggle);
            }
            
            const itemText = document.createElement('span');
            itemText.innerHTML = `[${i}]<span class="json-value-type">${valueType}</span>`;
            item.appendChild(itemText);
            
            item.onclick = function(e) {
                e.stopPropagation();
                document.querySelectorAll('.json-tree-item').forEach(el => el.classList.remove('active'));
                this.classList.add('active');
                document.getElementById('current-json-path').textContent = itemPath;
                if (!isComplex) {
                    document.getElementById('json-content').textContent = JSON.stringify(data[i], null, 2);
                } else {
                    document.getElementById('json-content').textContent = JSON.stringify(data[i], null, 2);
                }
            };
            
            if (isComplex) {
                const childContainer = document.createElement('div');
                childContainer.className = 'json-tree-children';
                childContainer.style.display = 'none';
                generateJsonTree(data[i], childContainer, itemPath);
                item.appendChild(childContainer);
            }
            
            list.appendChild(item);
        }
        
        container.appendChild(list);
    } else if (typeof data === 'object' && data !== null) {
        // Handle object
        const list = document.createElement('div');
        list.className = 'json-tree-children';
        
        for (const key in data) {
            const itemPath = path === '$' ? `$.${key}` : `${path}.${key}`;
            const item = document.createElement('div');
            item.className = 'json-tree-item';
            
            const valueType = typeof data[key];
            const isComplex = valueType === 'object' && data[key] !== null;
            
            if (isComplex) {
                const toggle = document.createElement('span');
                toggle.className = 'json-tree-toggle';
                toggle.textContent = '▶';
                toggle.onclick = function(e) {
                    e.stopPropagation();
                    const childContainer = this.parentNode.querySelector('.json-tree-children');
                    if (childContainer.style.display === 'none') {
                        childContainer.style.display = 'block';
                        this.textContent = '▼';
                    } else {
                        childContainer.style.display = 'none';
                        this.textContent = '▶';
                    }
                };
                item.appendChild(toggle);
            }
            
            const itemText = document.createElement('span');
            itemText.innerHTML = `<span class="json-key">${key}</span><span class="json-value-type">${valueType}</span>`;
            item.appendChild(itemText);
            
            item.onclick = function(e) {
                e.stopPropagation();
                document.querySelectorAll('.json-tree-item').forEach(el => el.classList.remove('active'));
                this.classList.add('active');
                document.getElementById('current-json-path').textContent = itemPath;
                if (!isComplex) {
                    document.getElementById('json-content').textContent = JSON.stringify(data[key], null, 2);
                } else {
                    document.getElementById('json-content').textContent = JSON.stringify(data[key], null, 2);
                }
            };
            
            if (isComplex) {
                const childContainer = document.createElement('div');
                childContainer.className = 'json-tree-children';
                childContainer.style.display = 'none';
                generateJsonTree(data[key], childContainer, itemPath);
                item.appendChild(childContainer);
            }
            
            list.appendChild(item);
        }
        
        container.appendChild(list);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    const editor = document.getElementById('sql-query');
    if (editor) {
        editor.addEventListener('input', updateLineNumbers);
        editor.addEventListener('scroll', function() {
            const lineNumbers = document.getElementById('line-numbers');
            if (lineNumbers) {
                lineNumbers.scrollTop = editor.scrollTop;
            }
        });
        
        // Initialize line numbers
        updateLineNumbers();
        
        // Also handle window resize which might affect editor size
        window.addEventListener('resize', updateLineNumbers);
    }
    
    // Initialize mode toggle
    toggleQueryMode();
    
    // Log for debugging
    console.log('DOMContentLoaded event fired, initializing SQL editor');
});

// Fallback form submission handler
document.addEventListener('DOMContentLoaded', function() {
    console.log('Setting up fallback form handler');
    setupFallbackFormHandler();
});

function setupFallbackFormHandler() {
    // Add a fallback vanilla JS form handler in case HTMX doesn't work
    const form = document.getElementById('sql-query-form');
    if (form) {
        console.log('Found form, adding fallback handler');
        
        form.addEventListener('submit', function(e) {
            console.log('Form submit intercepted by fallback handler');
            
            // Only intercept if we suspect HTMX isn't working
            const htmxWorking = typeof htmx !== 'undefined' && 
                               form.hasAttribute('hx-post') &&
                               document.querySelector('#sql-query-form[hx-post]');
                               
            if (!htmxWorking) {
                console.log('Using fallback submission mechanism');
                e.preventDefault();
                
                const query = document.getElementById('sql-query').value;
                const formData = new FormData();
                formData.append('query', query);
                
                fetch('/execute-query', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.text())
                .then(html => {
                    const resultDiv = document.getElementById('query-results');
                    if (resultDiv) {
                        resultDiv.innerHTML = html;
                        console.log('Results updated via fallback handler');
                    }
                })
                .catch(error => {
                    console.error('Error in fallback submission:', error);
                    alert('Error executing query. Check console for details.');
                });
            } else {
                console.log('HTMX appears to be working, using normal submission');
            }
        });
    }
}

// Call this function after any DOM updates that might affect the form
function reinitializePage() {
    console.log('Reinitializing page...');
    setupFallbackFormHandler();
    updateLineNumbers();
    
    // Make sure the mode toggle is correctly set
    toggleQueryMode();
    
    // Make sure HTMX is processing the page correctly
    if (typeof htmx !== 'undefined') {
        htmx.process(document.body);
    }
}

// Mode toggle function
function toggleQueryMode() {
    const form = document.getElementById('sql-query-form');
    const sqlLabel = document.getElementById('sql-mode-label');
    const nlLabel = document.getElementById('nl-mode-label');
    const isNLMode = document.getElementById('nl-toggle').checked;
    
    if (isNLMode) {
        form.classList.add('nl-mode');
        nlLabel.classList.add('active');
        sqlLabel.classList.remove('active');
        document.getElementById('sql-query').placeholder = "Ask a question about your data in plain English...";
    } else {
        form.classList.remove('nl-mode');
        sqlLabel.classList.add('active');
        nlLabel.classList.remove('active');
        document.getElementById('sql-query').placeholder = "SELECT * FROM table_name LIMIT 10;";
    }
}

// Handle translation form submission
function handleTranslateSubmit(event) {
    event.preventDefault();
    console.log("Translation button clicked");
    
    const isNLMode = document.getElementById('nl-toggle').checked;
    if (!isNLMode) {
        console.log("Not in NL mode, ignoring translate click");
        return;
    }
    
    const query = document.getElementById('sql-query').value;
    if (!query.trim()) {
        alert("Please enter a question first");
        return;
    }
    
    const formData = new FormData();
    formData.append('query', query);
    
    // Show loading state in the main query results area
    const resultsPanel = document.getElementById('query-results');
    resultsPanel.innerHTML = '<div class="p-4 text-center"><div class="animate-pulse">Translating your query...</div></div>';
    
    console.log("Sending translation request");
    
    // Use either htmx or fetch API
    if (typeof htmx !== 'undefined') {
        htmx.ajax('POST', '/translate-query', {
            target: '#query-results',
            swap: 'innerHTML',
            values: formData
        });
    } else {
        fetch('/translate-query', {
            method: 'POST', 
            body: formData
        })
        .then(response => response.text())
        .then(html => {
            resultsPanel.innerHTML = html;
        })
        .catch(error => {
            resultsPanel.innerHTML = `<div class="p-4 bg-red-50 text-red-700 rounded-lg">Error: ${error.message}</div>`;
        });
    }
}