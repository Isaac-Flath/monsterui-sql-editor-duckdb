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

// Clear editor and results
function clearEditor() {
    // Clear the SQL query field
    const editor = document.getElementById('sql-query');
    if (editor) {
        editor.value = '';
        updateLineNumbers();
    }
    
    // Clear the results panel
    const resultsPanel = document.getElementById('query-results');
    if (resultsPanel) {
        resultsPanel.innerHTML = '<div class="p-4 text-center text-gray-500">Results cleared. Execute a query to see results.</div>';
    }
    
    console.log('Editor and results cleared');
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

// Add query to history
function addQueryToHistory(query, timestamp) {
    // Create a unique ID for this query tab
    const tabId = 'query-tab-' + Date.now();
    const contentId = 'query-content-' + Date.now();
    
    // Get tabs container
    const tabsContainer = document.getElementById('query-tabs');
    if (!tabsContainer) {
        console.error('Query tabs container not found');
        return;
    }
    
    // Hide "no queries" message if shown
    const noQueriesMessage = document.getElementById('no-queries-message');
    if (noQueriesMessage) {
        noQueriesMessage.style.display = 'none';
    }
    
    // Format the query (truncate if too long)
    const queryText = query.length > 30 ? query.substring(0, 27) + '...' : query;
    
    // Create new tab
    const newTab = document.createElement('div');
    newTab.className = 'query-tab';
    newTab.id = tabId;
    newTab.innerHTML = `
        <span class="query-tab-text">${queryText}</span>
        <span class="query-tab-time">${timestamp}</span>
        <span class="query-tab-close" onclick="removeQueryTab('${tabId}', '${contentId}', event)">×</span>
    `;
    
    // Store query content in a data attribute
    newTab.setAttribute('data-query', query);
    
    // Add click handler to activate this tab
    newTab.addEventListener('click', function(e) {
        if (e.target.classList.contains('query-tab-close')) {
            return; // Don't activate when clicking the close button
        }
        
        activateQueryTab(tabId, contentId, query);
    });
    
    // Add to beginning of tabs
    if (tabsContainer.children.length > 0) {
        tabsContainer.insertBefore(newTab, tabsContainer.children[0]);
    } else {
        tabsContainer.appendChild(newTab);
    }
    
    // Store the current results in a hidden div
    const resultsPanel = document.getElementById('query-results');
    if (resultsPanel) {
        // Create a content container for this tab if it doesn't exist
        let contentContainer = document.getElementById(contentId);
        if (!contentContainer) {
            contentContainer = document.createElement('div');
            contentContainer.id = contentId;
            contentContainer.className = 'query-content';
            contentContainer.style.display = 'none';
            
            // Add this content container to a hidden container in the body
            let hiddenContainer = document.getElementById('hidden-results-container');
            if (!hiddenContainer) {
                hiddenContainer = document.createElement('div');
                hiddenContainer.id = 'hidden-results-container';
                hiddenContainer.style.display = 'none';
                document.body.appendChild(hiddenContainer);
            }
            hiddenContainer.appendChild(contentContainer);
        }
        
        // Copy current results to this container
        contentContainer.innerHTML = resultsPanel.innerHTML;
        console.log('Saved results for tab', tabId, 'content size:', contentContainer.innerHTML.length);
    }
    
    // Activate this tab
    activateQueryTab(tabId, contentId, query);
    
    // Limit to 10 tabs
    const tabs = tabsContainer.querySelectorAll('.query-tab');
    if (tabs.length > 10) {
        // Find the oldest tab (last one) and its content, and remove both
        const oldestTab = tabs[tabs.length - 1];
        const oldestContentId = 'query-content-' + oldestTab.id.replace('query-tab-', '');
        const oldestContent = document.getElementById(oldestContentId);
        
        if (oldestContent) {
            oldestContent.parentNode.removeChild(oldestContent);
        }
        oldestTab.parentNode.removeChild(oldestTab);
    }
}

// Activate a query tab
function activateQueryTab(tabId, contentId, query) {
    console.log('Activating tab:', tabId, 'with content:', contentId);
    
    // Deactivate all tabs
    document.querySelectorAll('.query-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Activate this tab
    const tab = document.getElementById(tabId);
    if (tab) {
        tab.classList.add('active');
    }
    
    // First update the SQL editor with this query
    const editor = document.getElementById('sql-query');
    if (editor) {
        editor.value = query;
        updateLineNumbers();
    }
    
    // Get the content and results panel
    const content = document.getElementById(contentId);
    const resultsPanel = document.getElementById('query-results');
    
    if (content && resultsPanel) {
        console.log('Found content and results panel, updating content');
        // Clear out existing results first
        resultsPanel.innerHTML = '';
        // Then replace with the content for this tab
        resultsPanel.innerHTML = content.innerHTML;
    } else {
        console.error('Missing content or results panel', contentId, resultsPanel);
        // If we're missing content, show a message
        if (resultsPanel) {
            resultsPanel.innerHTML = '<div class="p-4 text-center text-gray-500">Results not available. Execute the query again to see results.</div>';
        }
    }
}

// Remove a query tab
function removeQueryTab(tabId, contentId, event) {
    // Stop event propagation to prevent tab activation
    event.stopPropagation();
    
    // Remove the tab
    const tab = document.getElementById(tabId);
    if (tab) {
        // Check if it's the active tab
        const isActive = tab.classList.contains('active');
        
        // Get parent to check if there are other tabs
        const tabsContainer = tab.parentNode;
        
        // Remove the tab
        tab.parentNode.removeChild(tab);
        
        // Remove the content
        const content = document.getElementById(contentId);
        if (content) {
            content.parentNode.removeChild(content);
        }
        
        // If there are other tabs and this was the active one, activate the first one
        if (isActive && tabsContainer.children.length > 0) {
            // Find first actual tab (not the new tab button)
            const firstTab = tabsContainer.querySelector('.query-tab');
            if (firstTab) {
                const firstTabId = firstTab.id;
                const firstContentId = 'query-content-' + firstTabId.replace('query-tab-', '');
                const query = firstTab.getAttribute('data-query') || '';
                activateQueryTab(firstTabId, firstContentId, query);
            }
        } else if (tabsContainer.children.length === 0) {
            // If no tabs left, show no queries message
            const noQueriesMessage = document.getElementById('no-queries-message');
            if (noQueriesMessage) {
                noQueriesMessage.style.display = 'block';
            }
            
            // Clear results panel
            const resultsPanel = document.getElementById('query-results');
            if (resultsPanel) {
                resultsPanel.innerHTML = '<div class="p-4 text-center text-gray-500">No query results to display. Execute a query to see results.</div>';
            }
        }
    }
}

// Clear tab history
function clearQueryHistory() {
    const tabsContainer = document.getElementById('query-tabs');
    if (tabsContainer) {
        // Remove all tabs
        const tabs = tabsContainer.querySelectorAll('.query-tab');
        tabs.forEach(tab => {
            const contentId = 'query-content-' + tab.id.replace('query-tab-', '');
            const content = document.getElementById(contentId);
            if (content) {
                content.parentNode.removeChild(content);
            }
            tab.parentNode.removeChild(tab);
        });
        
        // Show no queries message
        const noQueriesMessage = document.getElementById('no-queries-message');
        if (noQueriesMessage) {
            noQueriesMessage.style.display = 'block';
        }
        
        // Clear results panel
        const resultsPanel = document.getElementById('query-results');
        if (resultsPanel) {
            resultsPanel.innerHTML = '<div class="p-4 text-center text-gray-500">No query results to display. Execute a query to see results.</div>';
        }
    }
}

// Check if a string is JSON
function isJsonString(str) {
    if (typeof str !== 'string') return false;
    
    // Quick check for JSON-like structure
    if (!(str.startsWith('{') && str.endsWith('}')) && 
        !(str.startsWith('[') && str.endsWith(']'))) {
        return false;
    }
    
    try {
        JSON.parse(str);
        return true;
    } catch (e) {
        return false;
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

// Copy JSON path to clipboard
function copyJsonPath() {
    const path = document.getElementById('current-json-path').textContent;
    navigator.clipboard.writeText(path).then(() => {
        alert('JSON path copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
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