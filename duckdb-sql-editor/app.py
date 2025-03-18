#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DuckDB SQL Editor with FastHTML and MonsterUI
"""

import os, json, duckdb, requests, atexit
from pathlib import Path
from dotenv import load_dotenv
from fasthtml import serve
from fasthtml.common import *
from monsterui.all import *
from db import DB_PATH, db, DatabaseManager

# Load environment variables
load_dotenv()

db = DatabaseManager()

def with_db_connection(default_value=None):
    """Decorator to handle database connections and error handling
    Args:
        default_value: Value to return if operation fails (default: None)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            db.connect(DB_PATH)
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                print(f"Error in {func.__name__}: {e}")
                return default_value
        return wrapper
    return decorator

@with_db_connection(default_value=[])
def get_table_names():
    """Get a list of table names from the database"""
    tables = db.connection.execute("SHOW TABLES").fetchall()
    return [table[0] for table in tables]

@with_db_connection(default_value=[])
def get_table_schema(table_name):
    """Get the schema for a specific table"""
    print(f"Fetching schema for table: {table_name}")
    schema = db.connection.execute(f"DESCRIBE {table_name}").fetchall()
    print(f"Schema for {table_name}: {len(schema)} columns")
    return schema

def reset_connection():
    """Reset the database connection if it becomes unresponsive"""
    global _db_connection
    
    print("Resetting database connection...")
    try:
        if _db_connection is not None:
            try: _db_connection.close()
            except Exception as e: print(f"Error closing existing connection: {e}")
            finally: _db_connection = None
        
        # Create a new connection
        db_path = Path(DB_PATH).resolve()
        print(f"Creating new database connection to {db_path}")
        _db_connection = duckdb.connect(str(db_path), read_only=True)
        
        # Test the connection
        _db_connection.execute("SELECT 1").fetchall()
        print("Connection reset successful")
        return True
    except Exception as e:
        print(f"Failed to reset connection: {e}")
        _db_connection = None
        return False

def execute_query(query):
    """Execute a SQL query and return the results"""
    def get_results(connection):
        """Helper to execute query and get results with column names"""
        result = connection.execute(query).fetchall()
        columns = []
        if connection.description is not None:
            columns = [col[0] for col in connection.description]
        return {"columns": columns, "data": result}

    db.connect(DB_PATH)
    try:
        print(f"Executing query: {query[:100]}...")
        return get_results(db.connection)

    except (duckdb.ConnectionException, duckdb.IOException) as conn_error:
        # Handle connection-specific issues
        print(f"Connection error: {conn_error}")
        print("Attempting to reset connection...")
        
        if reset_connection():
            try:
                db.connect(DB_PATH)
                print("Retrying query after connection reset...")
                return get_results(db.connection)
            except duckdb.Error as retry_error:
                print(f"Retry failed: {retry_error}")
                return {"error": f"Query failed after connection reset: {retry_error}", "columns": [], "data": []}
        return {"error": f"Database connection error: {conn_error}", "columns": [], "data": []}

    except duckdb.Error as query_error:
        # Handle query-specific errors (syntax errors, etc.)
        print(f"Query error: {query_error}")
        return {"error": str(query_error), "columns": [], "data": []}

    except Exception as unexpected_error:
        # Handle any unexpected errors not covered by DuckDB exceptions
        print(f"Unexpected error: {unexpected_error}")
        return {"error": f"An unexpected error occurred: {unexpected_error}", "columns": [], "data": []}

# Initialize the app with MonsterUI theme
app, rt = fast_app(hdrs=(*Theme.blue.headers(), Link(href='styles.css', rel="stylesheet"), Script(src='index.js')))

@rt('/')
def index():
    """Main page with SQL editor"""
    tables = get_table_names()
    print(f"Loaded {len(tables)} tables from database")
    
    # Pre-load schemas for all tables
    for table in tables:
        schema = get_table_schema(table)
        print(f"Pre-loaded schema for {table}: {len(schema)} columns")
    
    return Container(
            # Header with improved styling
            Div(
                Div(
                    H1("DuckDB SQL Editor", cls="text-2xl font-bold"),
                    
                    cls="flex-grow"
                ),
                Div(
                    P(f"Connected to: {DB_PATH}", cls="text-sm text-gray-500"),
                    P(f"Available Tables: {len(tables)}", cls="text-sm text-gray-500"),
                    Button(
                        "Change Database", 
                        cls=ButtonT.secondary + " text-xs px-2 py-1 mt-1",
                        onclick="console.log('Database button clicked'); openModal();"
                    ),
                    cls="text-right header-actions"
                ),
                cls="flex justify-between items-center py-4 border-b border-gray-200 mb-6"
            ),
            
            # Main content area wrapped in a main tag
            Main(
                # Reorganized main layout
                Div(
                    # First row with editor and database tables
                    Div(
                        # Left sidebar with database tables (moved to first position)
                        Div(
                            # Left panels container
                            Div(
                                # Database Tables section
                                Div(
                                    # Header
                                    Div(
                                        H3("Database Tables", cls="text-lg font-semibold"),
                                        P(f"{len(tables)} tables available", cls="text-xs text-gray-500"),
                                        cls="sidebar-section-heading"
                                    ),
                                    # Table list with inline schemas
                                    Div(
                                        *[Div(
                                            # Table header - clickable with toggle indicator
                                            Div(
                                                Div(
                                                    Strong(table, cls="block text-gray-800"),
                                                    Span(f"{len(get_table_schema(table))} columns", cls="column-count")
                                                ),
                                                Span("›", cls="toggle-indicator", id=f"toggle-{table}"),
                                                cls="table-header",
                                                id=f"table-header-{table}",
                                                onclick=f"toggleSchema('{table}')"
                                            ),
                                            # Schema container - hidden by default
                                            Div(
                                                get_table_schema_component(table),
                                                cls="schema-container",
                                                id=f"schema-{table}"
                                            ),
                                            cls="table-item"
                                        ) for table in tables],
                                        cls="schema-section"
                                    ),
                                    cls="border rounded-lg overflow-hidden bg-white shadow-sm h-full"
                                ),
                                cls="left-panels"
                            ),
                            cls="sidebar"
                        ),
                        
                        # SQL editor
                        Card(
                            Div(
                                H3("SQL Query", cls="text-lg font-semibold"),
                                P("Write your SQL query below", cls="text-sm text-gray-500"),
                                cls="flex justify-between items-center mb-3"
                            ),
                            
                            # Add mode toggle container
                            Div(
                                Span("SQL Mode", id="sql-mode-label", cls="mode-label active"),
                                Label(
                                    Input(type="checkbox", id="nl-toggle", onchange="toggleQueryMode()"),
                                    Span(cls="slider"),
                                    cls="switch mx-2"
                                ),
                                Span("Natural Language", id="nl-mode-label", cls="mode-label"),
                                Span("AI Powered", cls="nl-badge"),
                                cls="mode-toggle-container"
                            ),
                            
                            # SQL Query Form
                            Form(
                                Div(
                                    # Query container
                                    Div(
                                        # Editor wrapper to contain line numbers and editor
                                        Div(
                                            # Line numbers container
                                            Pre(id="line-numbers", cls="line-numbers"),
                                            
                                            # Improved SQL editor
                                            Textarea(
                                                id="sql-query",
                                                name="query",
                                                placeholder="SELECT * FROM table_name LIMIT 10;",
                                                cls="sql-editor with-line-numbers w-full h-80 p-3 resize-y"
                                            ),
                                            cls="editor-wrapper"
                                        ),
                                        cls="query-container relative mb-3"
                                    )
                                ),
                                Div(
                                    # SQL execution button
                                    Button("Execute Query", type="submit", 
                                          cls=ButtonT.primary + " px-6 py-2 execute-btn"),
                                    
                                    # Natural language translation button
                                    Button("Translate and run SQL", type="button", 
                                          cls="translate-btn",
                                          onclick="handleTranslateSubmit(event)"),
                                    cls="flex justify-end"
                                ),
                                hx_post="/execute-query",
                                hx_target="#query-results",
                                hx_swap="innerHTML",
                                hx_trigger="submit",
                                id="sql-query-form",
                                cls="mt-2"
                            ),
                            
                            # Remove the separate translation results container since we're using the main query results container
                            
                            cls="shadow-sm flex-1"
                        ),
                        cls="editor-row mb-2" # Reduced margin bottom here
                    ),
                    
                    # Second row with query results (full width)
                    Div(
                        # Query results with tabs
                        Card(
                            Div(
                                H3("Query Results", cls="text-lg font-semibold"),
                                cls="flex justify-between items-center mb-3"
                            ),
                            # Tabs for query history
                            Div(
                                id="query-tabs",
                                cls="query-tabs"
                            ),
                            # Hidden message for when no queries exist
                            P("No queries yet. Execute a query to start building history.", 
                              cls="text-sm text-gray-500 p-2 mx-2",
                              id="no-queries-message"),
                            # Query results container
                            Div(
                                id="query-results", 
                                cls="bg-white result-container query-result-panel p-4"
                            ),
                            cls="shadow-sm"
                        ),
                        cls="results-row flex-grow" # Added flex-grow to take up remaining space
                    ),
                    cls="main-layout"
                ),
                cls="flex-1"
            ),
            
            # Footer with improved styling - modified class
            DivFullySpaced(
                Div(Subtitle("Built with FastHTML, MonsterUI and DuckDB"),),
                DivRAligned(UkIconLink("github", href="https://github.com/AnswerDotAI/MonsterUI"),
                            UkIconLink("database", href="https://duckdb.org/docs/")),
                cls="p-4 footer"),
            
            # Modal backdrop (separate element)
            Div(
                id="modalBackdrop",
                cls="modal-backdrop",
                onclick="closeModal()"
            ),
            
            # Database selection modal container - simplified
            Div(
                id="modalContainer",
                cls="modal-container",
                style="background-color: white; border: 2px solid black;"
            ),
            
            
            # Modal script
            Script("""
                // Open the modal
                function openModal() {
                    console.log('Opening modal');
                    const backdrop = document.getElementById('modalBackdrop');
                    const container = document.getElementById('modalContainer');
                    
                    if (backdrop && container) {
                        console.log('Modal elements found, showing modal');
                        
                        // Force styles directly
                        backdrop.style.position = 'fixed';
                        backdrop.style.top = '0';
                        backdrop.style.left = '0';
                        backdrop.style.width = '100%';
                        backdrop.style.height = '100%';
                        backdrop.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
                        backdrop.style.zIndex = '9998';
                        backdrop.style.display = 'block';
                        
                        container.style.position = 'fixed';
                        container.style.top = '50%';
                        container.style.left = '50%';
                        container.style.transform = 'translate(-50%, -50%)';
                        container.style.backgroundColor = 'white';
                        container.style.border = '1px solid #ccc';
                        container.style.borderRadius = '8px';
                        container.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.1)';
                        container.style.zIndex = '9999';
                        container.style.width = '90%';
                        container.style.maxWidth = '500px';
                        container.style.minHeight = '300px'; 
                        container.style.maxHeight = '90vh';
                        container.style.overflowY = 'auto';
                        container.style.display = 'block';
                        container.style.padding = '20px';
                        
                        // Create modal content using innerHTML to ensure it's rendered
                        container.innerHTML = `
                            <div class="modal-header">
                                <h3 class="text-lg font-semibold">Connect to a DuckDB Database</h3>
                                <button class="text-gray-400 hover:text-gray-500 text-xl font-bold" onclick="closeModal()">×</button>
                            </div>
                            
                            <div class="modal-body">                                
                                <form id="upload-form" class="mb-4">
                                    <div class="form-group mb-3">
                                        <label for="db_file" class="block mb-1 font-medium">Choose File:</label>
                                        <input type="file" id="db_file" name="db_file" accept=".duckdb,.db" class="w-full px-3 py-2 border rounded">
                                    </div>
                                    
                                    <div class="flex justify-end mt-4">
                                        <button type="submit" id="upload-btn" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
                                            hx-post="/change-database" hx-target="#result-area" hx-swap="innerHTML" hx-encoding="multipart/form-data">Connect</button>
                                    </div>
                                </form>
                                <div id="result-area" class="mt-2"></div>
                            </div>
                        `;
                        
                        // Add htmx event handlers after content is injected
                        setupFormHandlers();
                        
                        document.body.style.overflow = 'hidden'; // Prevent scrolling
                        
                        // Debug info
                        console.log('Backdrop z-index:', getComputedStyle(backdrop).zIndex);
                        console.log('Modal z-index:', getComputedStyle(container).zIndex);
                        console.log('Backdrop display:', getComputedStyle(backdrop).display);
                        console.log('Modal display:', getComputedStyle(container).display);
                        console.log('Modal background-color:', getComputedStyle(container).backgroundColor);
                        console.log('Modal dimensions:', container.offsetWidth, 'x', container.offsetHeight);
                        console.log('Modal position:', container.offsetLeft, ',', container.offsetTop);
                        console.log('Modal has children:', container.children.length);
                    } else {
                        console.error('Modal elements not found!', {
                            backdrop: backdrop,
                            container: container
                        });
                    }
                }
                
                // Close the modal
                function closeModal() {
                    console.log('Closing modal');
                    const backdrop = document.getElementById('modalBackdrop');
                    const container = document.getElementById('modalContainer');
                    
                    // Check if we should reload the page due to database change
                    const resultArea = document.getElementById('result-area');
                    const shouldReload = resultArea && 
                        resultArea.textContent && 
                        resultArea.textContent.includes('Successfully connected to');
                    
                    if (backdrop && container) {
                        backdrop.style.display = 'none';
                        container.style.display = 'none';
                        document.body.style.overflow = ''; // Allow scrolling
                    }
                    
                    // Clear any previous messages
                    if (resultArea) {
                        resultArea.innerHTML = '';
                    }
                    
                    // If database was changed successfully, reload the page
                    if (shouldReload) {
                        console.log('Database changed successfully. Reloading page...');
                        window.location.reload();
                    }
                }
                
                // Initialize modal when the document is loaded
                document.addEventListener('DOMContentLoaded', function() {
                    console.log('Initializing modal');
                    const backdrop = document.getElementById('modalBackdrop');
                    const container = document.getElementById('modalContainer');
                    
                    if (backdrop && container) {
                        console.log('Modal elements found during initialization');
                        // Ensure z-index is set correctly
                        backdrop.style.zIndex = '9998';
                        container.style.zIndex = '9999';
                    } else {
                        console.error('Modal elements not found during initialization!');
                    }
                });
                
                // Setup htmx form handlers
                function setupFormHandlers() {
                    const uploadForm = document.getElementById('upload-form');
                    if (uploadForm) {
                        console.log('Found upload form, adding event listener');
                        uploadForm.addEventListener('submit', function(e) {
                            e.preventDefault();
                            
                            // Show loading state
                            const uploadBtn = document.getElementById('upload-btn');
                            if (uploadBtn) {
                                uploadBtn.disabled = true;
                                uploadBtn.innerHTML = 'Connecting...';
                            }
                            
                            const formData = new FormData(uploadForm);
                            const fileInput = document.getElementById('db_file');
                            
                            // Validate file extension
                            if (fileInput && fileInput.files.length > 0) {
                                const filename = fileInput.files[0].name;
                                if (!filename.endsWith('.duckdb') && !filename.endsWith('.db')) {
                                    document.getElementById('result-area').innerHTML = `
                                        <div class="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded relative">
                                            <strong>Error!</strong>
                                            <p>Please select a valid .duckdb or .db file</p>
                                        </div>
                                    `;
                                    if (uploadBtn) {
                                        uploadBtn.disabled = false;                                    }
                                    return;
                                }
                            }
                            
                            fetch('/change-database', {
                                method: 'POST',
                                body: formData
                            })
                            .then(response => response.json())
                            .then(data => {
                                const resultArea = document.getElementById('result-area');
                                if (data.success) {
                                    resultArea.innerHTML = `
                                        <div class="bg-green-50 border border-green-400 text-green-700 px-4 py-3 rounded relative">
                                            <strong>Success!</strong>
                                            <p>${data.message}</p>
                                            <p class="mt-2">Reloading page in 2 seconds...</p>
                                        </div>
                                    `;
                                    // Automatically reload after successful connection
                                    setTimeout(() => window.location.reload(), 2000);
                                } else {
                                    resultArea.innerHTML = `
                                        <div class="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded relative">
                                            <strong>Error!</strong>
                                            <p>${data.message}</p>
                                        </div>
                                    `;
                                    if (uploadBtn) {
                                        uploadBtn.disabled = false;
                                    }
                                }
                            })
                            .catch(error => {
                                document.getElementById('result-area').innerHTML = `
                                    <div class="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded relative">
                                        <strong>Error!</strong>
                                        <p>An unexpected error occurred</p>
                                    </div>
                                `;
                                if (uploadBtn) {
                                    uploadBtn.disabled = false;
                                    uploadBtn.innerHTML = 'Upload and Connect';
                                }
                            });
                        });
                    }
                }
                
                // Handle response from database change
                document.body.addEventListener('htmx:afterRequest', function(evt) {
                    if (evt.detail.target && evt.detail.target.id === 'result-area') {
                        if (evt.detail.successful) {
                            try {
                                const response = JSON.parse(evt.detail.xhr.response);
                                const resultArea = document.getElementById('result-area');
                                
                                if (response.success) {
                                    resultArea.innerHTML = `
                                        <div class="bg-green-50 border border-green-400 text-green-700 px-4 py-3 rounded relative">
                                            <strong>Success!</strong>
                                            <p>${response.message}</p>
                                            <p class="mt-2">
                                                <button onclick="reloadPage()" class="text-green-700 underline">
                                                    Reload the page to use the new database
                                                </button>
                                            </p>
                                        </div>
                                    `;
                                } else {
                                    resultArea.innerHTML = `
                                        <div class="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded relative">
                                            <strong>Error!</strong>
                                            <p>${response.message}</p>
                                        </div>
                                    `;
                                }
                            } catch (e) {
                                // If not JSON, display the raw response
                                document.getElementById('result-area').innerHTML = evt.detail.xhr.response;
                            }
                        }
                    }
                });
                
                function reloadPage() {
                    window.location.reload();
                }
            """),
            
            cls="mx-auto px-4 sm:px-6 lg:px-8 max-w-full w-[98%] container"
        )
    
    
def get_table_schema_component(table_name):
    """Generate a component showing the schema for a table"""
    if not table_name:
        return P("Invalid table name", cls="text-red-500 text-sm")
    
    try:
        schema = get_table_schema(table_name)
        if not schema:
            return P(f"No schema found for table: {table_name}", cls="text-red-500 text-sm")
        
        return Div(
            # Schema header with action button
            Div(
                P(f"Schema", cls="schema-header"),
               
                # Column list using a more compact design
                Ul(
                    *[Li(
                        Span(col[0], cls="column-name"),
                        Span(col[1], cls="column-type"),
                        Span("✓" if col[3] else "✗", 
                             cls=f"column-nullable {'text-green-600' if col[3] else 'text-red-500'}")
                    , cls="schema-column-item") for col in schema],
                    cls="schema-column-list"
                ),
                cls="p-2"
            )
        )
    except Exception as e:
        print(f"Error generating schema component for table {table_name}: {e}")
        return P(f"Error loading schema: {str(e)}", cls="text-red-500 text-sm")

@rt('/table/{table_name}')
def table_info(table_name):
    """Get schema information for a specific table"""
    if not table_name:
        return Div(P("Invalid table name", cls="text-red-500"))
    
    schema = get_table_schema(table_name)
    
    return Div(
        Div(
            H4(f"Schema for: {table_name}", cls="text-lg font-semibold"),
            Button("Query Table", 
                   cls=ButtonT.secondary + " text-sm px-3 py-1", 
                   hx_on=f"click: document.getElementById('sql-query').value = `SELECT * FROM {table_name} LIMIT 10;`; updateLineNumbers()"),
            cls="flex justify-between items-center mb-3"
        ),
        Div(
            Table(
                Thead(Tr(*[Th(col, cls="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider") 
                            for col in ["Column Name", "Type", "Nullable"]])),
                Tbody(*[Tr(
                        Td(col[0], cls="px-4 py-2 whitespace-nowrap font-medium text-gray-900"),
                        Td(col[1], cls="px-4 py-2 whitespace-nowrap font-mono text-xs text-gray-600 bg-gray-50"),
                        Td("Yes" if col[3] else "No", 
                           cls=f"px-4 py-2 whitespace-nowrap text-sm {'text-green-600' if col[3] else 'text-red-600'}")
                       ) for col in schema],
                      cls="divide-y divide-gray-200"
                ),
                cls="min-w-full divide-y divide-gray-200 table-fixed"
            ),
            cls="shadow overflow-hidden border-b border-gray-200 sm:rounded-lg bg-white"
        ),
        P("Click a column name to copy it to the query editor", cls="text-xs text-gray-500 mt-2"),
        cls="p-1"
    )

# Helper to check if a value might be JSON
def is_json(value):
    """Check if a value looks like it might be JSON"""
    if not isinstance(value, str):
        return False
    
    # Quick check for JSON-like structure
    value = value.strip()
    if not ((value.startswith('{') and value.endswith('}')) or 
            (value.startswith('[') and value.endswith(']'))):
        return False
    
    # Try to parse as JSON
    try:
        json.loads(value)
        return True
    except:
        return False

# Helper to truncate text for display
def truncate_text(text, max_length=100):
    """Truncate text to max_length and add ellipsis if needed"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + '...'

# Update the run_query function to handle JSON data
@rt('/execute-query', methods=['POST'])
async def run_query(request):
    """Execute a SQL query and return the results"""
    print("==== Starting run_query function ====")
    
    try:
        # Get form data correctly from the request
        print("Getting form data from request...")
        form_data = await request.form()
        query = form_data.get('query', '')
        print(f"Received query: {query[:50]}...")
        
        if not query.strip():
            print("Empty query received, returning error")
            return Div(
                Div(
                    Strong("Error: ", cls="font-bold"),
                    Span("Please enter a query"),
                    cls="p-4 bg-red-50 text-red-700 rounded-lg flex items-center"
                ),
                cls="my-4 single-query-result"
            )
        
        # Start timer for query execution
        import time
        import datetime
        import json
        start_time = time.time()
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        print("About to execute query...")
        results = execute_query(query)
        print("Query executed, processing results...")
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Properly escape the query for JavaScript
        # Use JSON encoding which handles all the escaping for us
        escaped_query = json.dumps(query)
        
        # JavaScript to add query to history and ensure form functionality persists
        history_script = Script(f"""
            // Add this query to history
            console.log("Adding query to history: {timestamp}");
            addQueryToHistory({escaped_query}, "{timestamp}");
            
            // CRITICAL: Re-initialize the form binding
            (function() {{
                console.log("Reinitializing form handlers");
                
                // Wait a moment for HTMX to complete its work
                setTimeout(function() {{
                    const form = document.querySelector('form[hx-post="/execute-query"]');
                    if (form) {{
                        console.log("Form found, ensuring htmx binding");
                        
                        // First, remove any existing event listeners by cloning the form
                        const parent = form.parentNode;
                        const clone = form.cloneNode(true);
                        parent.replaceChild(clone, form);
                        
                        // Re-process with HTMX
                        if (typeof htmx !== 'undefined') {{
                            console.log("Processing form with HTMX");
                            htmx.process(clone);
                        }}
                    }} else {{
                        console.error("Form not found!");
                    }}
                    
                    // Extra debug info
                    console.log("Form state:", {{
                        "formExists": !!document.querySelector('form[hx-post="/execute-query"]'),
                        "htmxLoaded": typeof htmx !== 'undefined'
                    }});
                    
                    // Use our more comprehensive page reinitialization
                    if (typeof reinitializePage === 'function') {{
                        reinitializePage();
                    }}
                }}, 10);
            }})();
        """)
        
        if "error" in results:
            print(f"Query error: {results['error']}")
            return Div(
                history_script,
                Div(
                    Strong("SQL Error: ", cls="font-bold"),
                    P(results["error"], cls="mt-2 font-mono text-sm p-3 bg-red-100 rounded overflow-x-auto"),
                    cls="p-4 bg-red-50 text-red-700 rounded-lg"
                ),
                cls="single-query-result"
            )
        
        # Limit display to 100 rows for performance
        display_data = results["data"][:100]
        total_rows = len(results["data"])
        
        if not display_data:
            print("Query returned no results")
            return Div(
                history_script,
                Div(
                    Strong("Query completed ", cls="font-bold"),
                    Span(f"in {execution_time:.2f}s"),
                    P("No results returned", cls="text-sm"),
                    cls="p-4 bg-green-50 text-green-700 rounded-lg"
                ),
                cls="single-query-result"
            )
            
        print(f"Processing {len(display_data)} rows for display")
        
        # Create table rows with special handling for JSON data
        rows = []
        for row_data in display_data:
            cells = []
            for i, cell in enumerate(row_data):
                cell_str = str(cell)
                column_name = results["columns"][i]
                
                # Check if cell could be JSON
                if is_json(cell_str):
                    # Create a JSON cell with prettifier and explorer
                    cells.append(
                        Td(
                            Div(
                                Div(
                                    Span(truncate_text(cell_str, 50), cls="json-text"),
                                    Span("JSON", cls="json-badge"),
                                    cls="cursor-pointer",
                                    onclick=f"toggleJsonPrettify(this)"
                                ),
                                Div(
                                    # This div will be filled with prettified JSON via JavaScript
                                    cls="json-prettified",
                                    style="display: none;"
                                ),
                                Button(
                                    "Explore JSON", 
                                    cls="mt-2 text-xs bg-blue-50 text-blue-600 px-2 py-1 rounded border border-blue-200 hover:bg-blue-100",
                                    onclick=f"openJsonExplorer({json.dumps(cell_str)}, '{column_name}')"
                                ),
                                data_json=cell_str,
                                cls="json-cell p-2"
                            ),
                            cls="whitespace-nowrap text-sm text-gray-900"
                        )
                    )
                else:
                    # Regular cell
                    cells.append(
                        Td(
                            cell_str, 
                            cls="px-4 py-2 whitespace-nowrap text-sm text-gray-900 truncate max-w-[300px]"
                        )
                    )
            
            rows.append(Tr(*cells, cls="hover:bg-gray-50"))
        
        print("Building final response...")
        
        # Build response
        response = Div(
            history_script,
            Div(
                Div(
                    Strong("Query successful ", cls="font-bold"),
                    Span(f"({execution_time:.2f}s)"),
                    cls="text-green-700"
                ),
                Div(
                    Span(f"Showing {len(display_data)} of {total_rows} rows", 
                       cls="text-sm text-gray-500"),
                    cls="mt-1"
                ),
                cls="mb-4 p-3 bg-green-50 rounded-lg"
            ),
            Div(
                Div(
                    Table(
                        Thead(
                            Tr(*[Th(col, cls="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider") 
                                for col in results["columns"]])
                        ),
                        Tbody(*rows, cls="bg-white divide-y divide-gray-200"),
                        cls="min-w-full divide-y divide-gray-200 result-table"
                    ),
                    cls="table-wrapper"
                ),
                cls="shadow border-b border-gray-200 rounded-lg"
            ),
            cls="py-2 single-query-result"
        )
        
        print("==== run_query function completed successfully ====")
        return response
        
    except Exception as e:
        import traceback
        print(f"=== CRITICAL ERROR IN run_query: {str(e)} ===")
        print(traceback.format_exc())
        
        # Return a user-friendly error message
        return Div(
            Div(
                Strong("Application Error: ", cls="font-bold"),
                P(f"An unexpected error occurred: {str(e)}", 
                  cls="mt-2 font-mono text-sm p-3 bg-red-100 rounded overflow-x-auto"),
                cls="p-4 bg-red-50 text-red-700 rounded-lg"
            ),
            cls="my-4 single-query-result"
        )

@rt('/debug', methods=['GET', 'POST'])
async def debug(request):
    """Debug endpoint to verify the app is still accepting requests"""
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    request_info = {
        "timestamp": timestamp,
        "method": "GET" if request.method == "GET" else "POST",
        "headers": dict(request.headers),
    }
    
    print(f"Debug endpoint accessed: {timestamp}")
    
    return Div(
        H3("App is Running", cls="text-lg font-semibold text-green-600"),
        P(f"Current time: {timestamp}", cls="text-sm"),
        P(f"Request method: {request_info['method']}", cls="text-sm"),
        P("This endpoint confirms the application is still accepting requests.", cls="mt-2 text-sm"),
        Button("Return to Editor", cls=ButtonT.secondary, 
               onclick="window.location.href='/'"),
        cls="p-4 bg-white shadow rounded-lg"
    )

@rt('/reset-connection', methods=['GET'])
async def reset_connection_endpoint(request):
    """Endpoint to reset the database connection"""
    success = reset_connection()
    
    if success:
        return Div(
            H3("Connection Reset Successful", cls="text-lg font-semibold text-green-600"),
            P("The database connection has been successfully reset.", cls="text-sm"),
            Button("Return to Editor", cls=ButtonT.secondary, 
                   onclick="window.location.href='/'"),
            cls="p-4 bg-white shadow rounded-lg"
        )
    else:
        return Div(
            H3("Connection Reset Failed", cls="text-lg font-semibold text-red-600"),
            P("Failed to reset the database connection. Check server logs for details.", 
              cls="text-sm"),
            Button("Try Again", cls=ButtonT.destructive, 
                   onclick="window.location.reload()"),
            Button("Return to Editor", cls=ButtonT.secondary, 
                   onclick="window.location.href='/'"),
            cls="p-4 bg-white shadow rounded-lg"
        )

@rt('/change-database', methods=['POST'])
async def change_database_endpoint(request):
    """Endpoint to change the database file by uploading a new one"""
    try:
        # Get the form data
        form_data = await request.form()
        
        # Handle file upload
        if 'db_file' in form_data:
            file = form_data['db_file']
            if not file.filename:
                return {"success": False, "message": "No file selected"}
            
            # Validate file extension
            if not (file.filename.endswith('.duckdb') or file.filename.endswith('.db')):
                return {"success": False, "message": "Invalid file type. Please upload a .duckdb or .db file"}
            
            # Create a temp directory if it doesn't exist
            temp_dir = Path("./temp_db")
            temp_dir.mkdir(exist_ok=True)
            
            # Save the file
            file_path = temp_dir / file.filename
            with open(file_path, 'wb') as f:
                f.write(await file.read())
            
            # Try to connect to the new database
            success, error = reset_with_new_db(str(file_path))
            if success:
                return {"success": True, "message": f"Successfully connected to {file.filename}"}
            else:
                # Clean up the file if connection failed
                if file_path.exists():
                    file_path.unlink()
                return {"success": False, "message": f"Failed to connect: {error}"}
        else:
            return {"success": False, "message": "No file uploaded"}
    except Exception as e:
        print(f"Error in change-database: {e}")
        return {"success": False, "message": f"An error occurred: {str(e)}"}

# Function to clean up resources
def cleanup_resources():
    """Close database connection and clean up resources"""
    global _db_connection
    if _db_connection is not None:
        print("Closing database connection on shutdown")
        try:
            _db_connection.close()
            _db_connection = None
        except Exception as e:
            print(f"Error closing database connection: {e}")
    
    # Clean up temporary database directory
    try:
        temp_dir = Path("./temp_db")
        if temp_dir.exists():
            import shutil
            print("Cleaning up temporary database directory")
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Error cleaning up temporary files: {e}")

def get_database_schema_info():
    """Get comprehensive schema information for all tables to inform AI translation"""
    tables = get_table_names()
    schema_info = {}
    
    # Process all tables
    for table in tables:
        try:
            # Get schema
            schema = get_table_schema(table)
            
            # Extract column names
            column_names = [col[0] for col in schema]
            
            # Initialize table info with columns
            schema_info[table] = {
                "columns": [{"name": col[0], "type": col[1], "nullable": col[3]} for col in schema],
            }
            
        except Exception as e:
            print(f"Error getting schema info for table {table}: {e}")
            schema_info[table] = {"error": str(e)}
    
    return schema_info

def format_for_openai(schema_info):
    """Format schema info into a more compact, readable text format for OpenAI"""
    formatted_text = []
    
    for table_name, table_info in schema_info.items():
        formatted_text.append(f"TABLE: {table_name}")
        
        # Format columns
        formatted_text.append("COLUMNS:")
        for col in table_info.get('columns', []):
            nullable = "NULL" if col.get('nullable', False) else "NOT NULL"
            formatted_text.append(f"  - {col['name']} ({col['type']}, {nullable})")
        
        # Format sample data if available
        sample_data = table_info.get('sample_data', [])
        if sample_data:
            formatted_text.append(f"\nSAMPLE DATA ({len(sample_data)} rows):")
            
            # Create a compact representation of each row
            for i, row in enumerate(sample_data):
                row_str = []
                for col, val in row.items():
                    # Truncate long values
                    if len(val) > 50:
                        val = val[:47] + "..."
                    row_str.append(f"{col}={val}")
                
                formatted_text.append(f"  ROW {i+1}: {', '.join(row_str)}")
    
    return "\n".join(formatted_text)

def translate_natural_language_to_sql(natural_language_query):
    """Translate a natural language query to DuckDB SQL using OpenAI"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "OpenAI API key not configured. Please add OPENAI_API_KEY to your .env file."}
    
    try:
        # Get database schema info
        schema_info = get_database_schema_info()
        
        # Format the schema info for OpenAI in a more compact way
        formatted_schema = format_for_openai(schema_info)
        
        # Log the size of different components
        schema_json_size = len(json.dumps(schema_info, indent=2))
        formatted_schema_size = len(formatted_schema)
        query_size = len(natural_language_query)
        
        print("\n=== DATA SIZE ANALYSIS ===")
        print(f"Original JSON schema size: {schema_json_size} characters")
        print(f"Formatted schema size: {formatted_schema_size} characters")
        print(f"Size reduction: {schema_json_size - formatted_schema_size} characters ({(schema_json_size - formatted_schema_size) / schema_json_size * 100:.1f}%)")
        print(f"Query size: {query_size} characters")
        print(f"Total content size: {formatted_schema_size + query_size + 100} characters (approx)")  # 100 for the template text
        
        # Log schema details
        if 'requests' in schema_info:
            columns_count = len(schema_info['requests'].get('columns', []))
            sample_rows = len(schema_info['requests'].get('sample_data', []))
            print(f"Requests table: {columns_count} columns in schema, {sample_rows} sample rows")
        
        # Create the content for sending to OpenAI
        prompt_content = f"""Database Schema:
{formatted_schema}

Natural Language Query:
{natural_language_query}

Translate this into a valid DuckDB SQL query:"""
        
        # Log the data being sent to OpenAI
        print("\n=== DATA SENT TO OPENAI ===")
        print(prompt_content[:500] + "..." if len(prompt_content) > 500 else prompt_content)
        print(f"\n=== TOTAL LENGTH: {len(prompt_content)} characters ===")
        
        # Construct the prompt for OpenAI
        prompt = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": """You are a DuckDB SQL expert. Translate natural language queries into valid DuckDB SQL queries.
Use the database schema and sample data provided to inform your translations.
If you need information about DuckDB SQL syntax or specific functions, consult https://duckdb.org/llms.txt
Always use date formatting functions from https://duckdb.org/docs/stable/sql/functions/date.html when dealing with dates or timestamps.
Return ONLY the SQL query NEVER ANYTHING ELSE like explanations or markdown formatting or ticks"""},
                {"role": "user", "content": prompt_content}
            ]
        }
        
        # Estimate token count (very rough approximation)
        estimated_tokens = len(prompt_content) / 4 + 100  # 4 chars per token + 100 for system message
        print(f"Estimated tokens: ~{int(estimated_tokens)}")
        
        # Call OpenAI API
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=prompt
        )
        
        if response.status_code != 200:
            return {"error": f"OpenAI API error: {response.text}"}
        
        # Extract the SQL query from the response
        result = response.json()
        sql_query = result["choices"][0]["message"]["content"].strip()
        
        # Strip any markdown code formatting (```SQL, ```, etc.)
        # Remove opening code block markers like ```sql, ```SQL, or just ```
        if sql_query.startswith("```"):
            # Find the first line break which would be after the ```sql or similar
            first_line_break = sql_query.find('\n')
            if first_line_break != -1:
                sql_query = sql_query[first_line_break+1:]
            else:
                # If no line break, just remove the first three backticks
                sql_query = sql_query[3:]
        
        # Remove closing code block markers
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        
        # Final trimming to remove any extra whitespace
        sql_query = sql_query.strip()
        
        # Log the generated SQL query
        print("\n=== GENERATED SQL QUERY ===")
        print(sql_query)
        print("===========================\n")
        
        return {"sql": sql_query}
    
    except Exception as e:
        import traceback
        print(f"Error translating query: {e}")
        print(traceback.format_exc())
        return {"error": f"Translation error: {str(e)}"}

@rt('/translate-query', methods=['POST'])
async def translate_query_endpoint(request):
    """Endpoint to translate natural language to SQL and automatically execute it"""
    print("==== Starting translate_query endpoint ====")
    
    try:
        # Get form data
        form_data = await request.form()
        natural_language_query = form_data.get('query', '')
        print(f"Received natural language query: {natural_language_query[:100]}...")
        
        if not natural_language_query.strip():
            return Div(
                Strong("Error: ", cls="font-bold"),
                Span("Please enter a query"),
                cls="p-4 bg-red-50 text-red-700 rounded-lg flex items-center"
            )
        
        # Translate the query
        print("Translating query...")
        result = translate_natural_language_to_sql(natural_language_query)
        
        if "error" in result:
            print(f"Translation error: {result['error']}")
            return Div(
                Strong("Translation Error: ", cls="font-bold"),
                P(result["error"], cls="mt-2 font-mono text-sm p-3 bg-red-100 rounded overflow-x-auto"),
                cls="p-4 bg-red-50 text-red-700 rounded-lg"
            )
        
        # Get the SQL query and add the original natural language as a comment
        sql_query = f"-- Natural Language: {natural_language_query}\n\n{result['sql']}"
        print(f"Successfully translated to SQL: {sql_query[:100]}...")
        
        # Update the SQL editor with the translated query
        import json
        sql_query_escaped = json.dumps(sql_query)
        
        # Execute the query (use the actual SQL part, not the comment)
        print("Automatically executing the translated query...")
        execution_results = execute_query(result["sql"])
        
        # Generate timestamp for query history
        import datetime
        import time
        start_time = time.time()
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        execution_time = time.time() - start_time
        
        # JavaScript to add query to history
        history_script = Script(f"""
            // Update the SQL editor with the translated query
            document.getElementById('sql-query').value = {sql_query_escaped};
            updateLineNumbers();
            
            // Add this query to history
            console.log("Adding translated query to history: {timestamp}");
            addQueryToHistory({sql_query_escaped}, "{timestamp}");
            
            // CRITICAL: Re-initialize the form binding
            (function() {{
                console.log("Reinitializing form handlers");
                
                // Wait a moment for HTMX to complete its work
                setTimeout(function() {{
                    const form = document.querySelector('form[hx-post="/execute-query"]');
                    if (form) {{
                        console.log("Form found, ensuring htmx binding");
                        
                        // First, remove any existing event listeners by cloning the form
                        const parent = form.parentNode;
                        const clone = form.cloneNode(true);
                        parent.replaceChild(clone, form);
                        
                        // Re-process with HTMX
                        if (typeof htmx !== 'undefined') {{
                            console.log("Processing form with HTMX");
                            htmx.process(clone);
                        }}
                    }} else {{
                        console.error("Form not found!");
                    }}
                    
                    // Extra debug info
                    console.log("Form state:", {{
                        "formExists": !!document.querySelector('form[hx-post="/execute-query"]'),
                        "htmxLoaded": typeof htmx !== 'undefined'
                    }});
                    
                    // Use our more comprehensive page reinitialization
                    if (typeof reinitializePage === 'function') {{
                        reinitializePage();
                    }}
                }}, 10);
            }})();
        """)
        
        # Display error if there was a problem executing the query
        if "error" in execution_results:
            print(f"Query execution error: {execution_results['error']}")
            return Div(
                history_script,
                Div(
                    Strong("SQL Error: ", cls="font-bold"),
                    P(execution_results["error"], cls="mt-2 font-mono text-sm p-3 bg-red-100 rounded overflow-x-auto"),
                    cls="p-4 bg-red-50 text-red-700 rounded-lg"
                ),
                cls="single-query-result"
            )
        
        # Process results similar to run_query function
        # Limit display to 100 rows for performance
        display_data = execution_results["data"][:100]
        total_rows = len(execution_results["data"])
        
        if not display_data:
            print("Query returned no results")
            return Div(
                history_script,
                Div(
                    Strong("Query completed ", cls="font-bold"),
                    Span(f"in {execution_time:.2f}s"),
                    P("No results returned", cls="text-sm"),
                    cls="p-4 bg-green-50 text-green-700 rounded-lg"
                ),
                cls="single-query-result"
            )
        
        print(f"Processing {len(display_data)} rows for display")
        
        # Create table rows with special handling for JSON data
        rows = []
        for row_data in display_data:
            cells = []
            for i, cell in enumerate(row_data):
                cell_str = str(cell)
                column_name = execution_results["columns"][i]
                
                # Check if cell could be JSON
                if is_json(cell_str):
                    # Create a JSON cell with prettifier and explorer
                    cells.append(
                        Td(
                            Div(
                                Div(
                                    Span(truncate_text(cell_str, 50), cls="json-text"),
                                    Span("JSON", cls="json-badge"),
                                    cls="cursor-pointer",
                                    onclick=f"toggleJsonPrettify(this)"
                                ),
                                Div(
                                    # This div will be filled with prettified JSON via JavaScript
                                    cls="json-prettified",
                                    style="display: none;"
                                ),
                                Button(
                                    "Explore JSON", 
                                    cls="mt-2 text-xs bg-blue-50 text-blue-600 px-2 py-1 rounded border border-blue-200 hover:bg-blue-100",
                                    onclick=f"openJsonExplorer({json.dumps(cell_str)}, '{column_name}')"
                                ),
                                data_json=cell_str,
                                cls="json-cell p-2"
                            ),
                            cls="whitespace-nowrap text-sm text-gray-900"
                        )
                    )
                else:
                    # Regular cell
                    cells.append(
                        Td(
                            cell_str, 
                            cls="px-4 py-2 whitespace-nowrap text-sm text-gray-900 truncate max-w-[300px]"
                        )
                    )
            
            rows.append(Tr(*cells, cls="hover:bg-gray-50"))
        
        # Build final response using the same format as regular SQL queries
        return Div(
            history_script,
            Div(
                Div(
                    Strong("Query successful ", cls="font-bold"),
                    Span(f"({execution_time:.2f}s)"),
                    cls="text-green-700"
                ),
                Div(
                    Span(f"Showing {len(display_data)} of {total_rows} rows", 
                       cls="text-sm text-gray-500"),
                    cls="mt-1"
                ),
                cls="mb-4 p-3 bg-green-50 rounded-lg"
            ),
            Div(
                Div(
                    Table(
                        Thead(
                            Tr(*[Th(col, cls="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider") 
                                for col in execution_results["columns"]])
                        ),
                        Tbody(*rows, cls="bg-white divide-y divide-gray-200"),
                        cls="min-w-full divide-y divide-gray-200 result-table"
                    ),
                    cls="table-wrapper"
                ),
                cls="shadow border-b border-gray-200 rounded-lg"
            ),
            cls="py-2 single-query-result"
        )
        
    except Exception as e:
        import traceback
        print(f"=== CRITICAL ERROR IN translate_query: {str(e)} ===")
        print(traceback.format_exc())
        
        return Div(
            Strong("Application Error: ", cls="font-bold"),
            P(f"An unexpected error occurred: {str(e)}", 
              cls="mt-2 font-mono text-sm p-3 bg-red-100 rounded overflow-x-auto"),
            cls="p-4 bg-red-50 text-red-700 rounded-lg"
        )

if __name__ == "__main__":
    # Register cleanup function to run on exit
    atexit.register(cleanup_resources)
    serve() 