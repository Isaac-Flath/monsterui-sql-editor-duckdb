/**
 * DuckDB SQL Editor JavaScript Functions
 */

// Editor mode toggle
function toggleEditorMode() {
    const form = document.getElementById('query-form');
    const modeToggle = document.getElementById('mode-toggle');
    const modeLabel = document.getElementById('nl-mode-label');
    
    if (modeToggle.checked) {
        form.classList.add('nl-mode');
        modeLabel.classList.add('active');
    } else {
        form.classList.remove('nl-mode');
        modeLabel.classList.remove('active');
    }
}

// Line numbers for the editor
function updateLineNumbers() {
    const editor = document.getElementById('sql-editor');
    const lineNumbers = document.getElementById('line-numbers');
    
    if (!editor || !lineNumbers) return;
    
    const lines = editor.value.split('\n');
    const count = lines.length;
    
    let html = '';
    for (let i = 1; i <= count; i++) {
        html += `<div>${i}</div>`;
    }
    
    lineNumbers.innerHTML = html;
}

// Initialize editor
function initEditor() {
    const editor = document.getElementById('sql-editor');
    
    if (editor) {
        editor.addEventListener('input', updateLineNumbers);
        editor.addEventListener('scroll', function() {
            const lineNumbers = document.getElementById('line-numbers');
            if (lineNumbers) {
                lineNumbers.scrollTop = editor.scrollTop;
            }
        });
        
        // Initial line numbers
        updateLineNumbers();
    }
}

// Toggle schema visibility
function toggleSchema(tableName) {
    const schemaContainer = document.getElementById(`schema-${tableName}`);
    
    if (schemaContainer) {
        schemaContainer.classList.toggle('open');
        
        // Update the button icon
        const tableItem = document.getElementById(`table-item-${tableName}`);
        if (tableItem) {
            const button = tableItem.querySelector('button');
            if (button) {
                const icon = button.querySelector('i');
                if (icon) {
                    if (schemaContainer.classList.contains('open')) {
                        icon.className = 'uk-icon-chevron-up';
                    } else {
                        icon.className = 'uk-icon-chevron-down';
                    }
                }
            }
        }
    }
}

// Query history tabs
function createQueryTab(query) {
    const tabsContainer = document.getElementById('query-tabs');
    if (!tabsContainer) return;
    
    // Generate a unique ID for this tab
    const tabId = 'query-tab-' + Date.now();
    const contentId = 'query-content-' + Date.now();
    
    // Create the tab
    const tab = document.createElement('div');
    tab.id = tabId;
    tab.className = 'query-tab';
    tab.innerHTML = `
        <span class="tab-title">${truncateText(query, 30)}</span>
        <button class="tab-close" onclick="removeQueryTab('${tabId}', '${contentId}')">×</button>
    `;
    
    // Add click handler to activate this tab
    tab.addEventListener('click', function(e) {
        if (e.target.className !== 'tab-close') {
            activateQueryTab(tabId, contentId, query);
        }
    });
    
    // Add to the beginning of the tabs container
    tabsContainer.insertBefore(tab, tabsContainer.firstChild);
    
    // Save current results
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
    // Deactivate all tabs
    document.querySelectorAll('.query-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Activate this tab
    const tab = document.getElementById(tabId);
    if (tab) {
        tab.classList.add('active');
    }
    
    // Show this tab's content
    const resultsPanel = document.getElementById('query-results');
    const contentContainer = document.getElementById(contentId);
    
    if (resultsPanel && contentContainer) {
        resultsPanel.innerHTML = contentContainer.innerHTML;
    }
    
    // Update the editor with this query
    const editor = document.getElementById('sql-editor');
    if (editor) {
        editor.value = query;
        updateLineNumbers();
    }
}

// Remove a query tab
function removeQueryTab(tabId, contentId) {
    const tab = document.getElementById(tabId);
    const content = document.getElementById(contentId);
    
    if (tab) {
        const isActive = tab.classList.contains('active');
        const nextTab = tab.nextElementSibling || tab.previousElementSibling;
        
        tab.parentNode.removeChild(tab);
        
        if (content) {
            content.parentNode.removeChild(content);
        }
        
        // If this was the active tab, activate the next one
        if (isActive && nextTab) {
            const nextTabId = nextTab.id;
            const nextContentId = 'query-content-' + nextTabId.replace('query-tab-', '');
            
            // Get the query from the tab title
            const tabTitle = nextTab.querySelector('.tab-title');
            const query = tabTitle ? tabTitle.getAttribute('data-query') || tabTitle.textContent : '';
            
            activateQueryTab(nextTabId, nextContentId, query);
        }
    }
    
    // Prevent event propagation
    event.stopPropagation();
}

// Database modal
function openDatabaseModal() {
    const modal = document.getElementById('database-modal');
    const backdrop = document.getElementById('modal-backdrop');
    
    if (modal && backdrop) {
        modal.classList.remove('hidden');
        backdrop.classList.remove('hidden');
    }
}

function closeDatabaseModal() {
    const modal = document.getElementById('database-modal');
    const backdrop = document.getElementById('modal-backdrop');
    
    if (modal && backdrop) {
        modal.classList.add('hidden');
        backdrop.classList.add('hidden');
    }
}

// JSON viewer
function showJsonViewer(jsonData) {
    try {
        const data = JSON.parse(jsonData);
        
        // Create modal
        let modal = document.getElementById('json-viewer-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'json-viewer-modal';
            modal.className = 'fixed inset-0 flex items-center justify-center z-50';
            document.body.appendChild(modal);
        }
        
        modal.innerHTML = `
            <div class="fixed inset-0 bg-black bg-opacity-50" onclick="closeJsonViewer()"></div>
            <div class="bg-white rounded-lg shadow-lg w-full max-w-4xl max-h-[80vh] overflow-auto relative">
                <div class="flex justify-between items-center p-4 border-b">
                    <h3 class="text-lg font-semibold">JSON Viewer</h3>
                    <button class="close-modal-btn" onclick="closeJsonViewer()">×</button>
                </div>
                <div class="p-4 json-viewer-content">
                    <div id="json-tree" class="json-tree"></div>
                </div>
            </div>
        `;
        
        // Generate JSON tree
        const jsonTree = document.getElementById('json-tree');
        generateJsonTree(data, jsonTree, '$');
        
        // Add copy button
        const copyBtn = document.createElement('button');
        copyBtn.className = 'json-copy-btn';
        copyBtn.textContent = 'Copy JSON';
        copyBtn.onclick = function() {
            navigator.clipboard.writeText(JSON.stringify(data, null, 2))
                .then(() => {
                    copyBtn.textContent = 'Copied!';
                    setTimeout(() => {
                        copyBtn.textContent = 'Copy JSON';
                    }, 2000);
                });
        };
        
        jsonTree.appendChild(copyBtn);
        
        // Show modal
        modal.style.display = 'flex';
    } catch (e) {
        console.error('Error parsing JSON:', e);
    }
}

function closeJsonViewer() {
    const modal = document.getElementById('json-viewer-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function generateJsonTree(data, container, path) {
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
            itemText.innerHTML = `<span class="json-key">${i}</span><span class="json-value-type">${valueType}</span>`;
            item.appendChild(itemText);
            
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
            
            if (isComplex) {
                const childContainer = document.createElement('div');
                childContainer.className = 'json-tree-children';
                childContainer.style.display = 'none';
                generateJsonTree(data[key], childContainer, itemPath);
                item.appendChild(childContainer);
            } else {
                const valueSpan = document.createElement('span');
                valueSpan.className = 'json-value';
                valueSpan.textContent = data[key];
                item.appendChild(valueSpan);
            }
            
            list.appendChild(item);
        }
        
        container.appendChild(list);
    }
}

// Helper functions
function truncateText(text, maxLength) {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initEditor();
}); 