#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DuckDB SQL Editor with FastHTML and MonsterUI
"""

import os, json, requests, atexit
from pathlib import Path
from dotenv import load_dotenv
from fasthtml import serve
from fasthtml.common import *
from monsterui.all import *
from db import DB_PATH, db, DatabaseManager, cleanup_resources
import json
import time
# Load environment variables
load_dotenv()

db = DatabaseManager()

def ErrorDiv(*args, **kwargs): return Div(*args, cls="p-4 bg-red-50 text-red-700 rounded-lg", **kwargs)

app, rt = fast_app(hdrs=(*Theme.blue.headers(), Link(href='styles.css', rel="stylesheet"), Script(src='index.js')))

def get_table_sidebar_component(table_name):
    return Div(
        Div(
            # Table header with toggle
            Div(
                DivFullySpaced(
                    Strong(table_name, cls=TextT.gray),
                    Subtitle(f"{len(db.get_table_schema(table_name))} columns", cls=TextT.xs),
                    cls="px-3 py-2 hover:bg-gray-50 cursor-pointer",
                    data_uk_toggle=f"target: #schema-{table_name}"),
                cls="border-b"),
            # Schema container - hidden by default
            Div(get_table_schema_component(table_name),
                cls="p-2 bg-gray-50",
                id=f"schema-{table_name}",
                hidden=True),
            cls="bg-white"))

@rt('/')
def index():
    """Main page with SQL editor"""
    tables = db.get_table_names()
    print(f"Loaded {len(tables)} tables from database")
    
    # Pre-load schemas for all tables
    for table in tables:
        schema = db.get_table_schema(table)
        print(f"Pre-loaded schema for {table}: {len(schema)} columns")
    
    return Container(
            # Header with improved styling
            DivFullySpaced(
                H3("DuckDB SQL Editor"),
                DivRAligned(
                    Subtitle(f"Connected to: {DB_PATH}"),
                    Subtitle(f"Available Tables: {len(tables)}"),
                    Button("Change Database", cls=ButtonT.secondary, data_uk_toggle="#change-database-modal")),
                cls='p-4 mb-4'),
            
            # Main content area wrapped in a main tag
            Main(
                # Reorganized main layout
                Div(
                    # First row with editor and database tables
                    Div(
                        # Left sidebar with database tables (moved to first position)
                        Div(
                            DivFullySpaced(
                                Strong("Database Tables"),
                                Subtitle(f"{len(tables)} tables available"),
                                cls='p-2'),
                            # Table list with inline schemas
                            Div(*[get_table_sidebar_component(table_name) for table_name in tables], cls="schema-section"),
                            cls="border rounded-lg overflow-hidden bg-white shadow-sm h-full"),
                        
                        # SQL editor
                        Card(
                            DivFullySpaced(
                                H5("SQL Query"),
                                Subtitle("Write your SQL query below")),
                            
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
                    
                        # Query results with tabs
                    Card(
                        Div(H3("Query Results", cls="text-lg font-semibold"),
                            cls="flex justify-between items-center mb-3"),
                        # Tabs for query history
                        Div(id="query-tabs", cls="query-tabs"),
                        # Hidden message for when no queries exist
                        Subtitle("No queries yet. Execute a query to start building history.", 
                            cls=TextT.sm, id="no-queries-message"),
                        # Query results container
                        Div(id="query-results", 
                            cls="bg-white result-container query-result-panel p-4")),
                    cls="flex flex-col gap-4"
                ),
                cls="flex-1"
            ),
            
            # Footer with improved styling - modified class
            DivFullySpaced(
                Div(Subtitle("Built with FastHTML, MonsterUI and DuckDB"),),
                DivRAligned(UkIconLink("github", href="https://github.com/AnswerDotAI/MonsterUI"),
                            UkIconLink("database", href="https://duckdb.org/docs/")),
                cls="p-4 border-t border-gray-200"),
                Modal(
                    H3("Connect to a DuckDB Database", cls="text-lg font-semibold"),
                    ModalCloseButton(),
                    UploadZone(DivCentered(Span("Upload Zone"), UkIcon("upload")), id='db_file', name='db_file', accept=".duckdb,.db"),
                    Button("Connect", type="submit", id="upload-btn", cls=ButtonT.primary),
                    id='change-database-modal'),
            cls="max-w-full w-[98%] min-h-screen flex flex-col")

def get_table_schema_component(table_name):
    """Generate a component showing the schema for a table"""
    if not table_name:
        return P("Invalid table name", cls="text-red-500 text-sm")
    
    try:
        schema = db.get_table_schema(table_name)
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
    
    schema = db.get_table_schema(table_name)
    
    return Div(
        Div(
            H4(f"Schema for: {table_name}", cls="text-lg font-semibold"),
            Button(
                "Query Table", 
                cls=ButtonT.secondary + " text-sm px-3 py-1", 
                hx_on=f"click: document.getElementById('sql-query').value = `SELECT * FROM {table_name} LIMIT 10;`; updateLineNumbers()"
            ),
            cls="flex justify-between items-center mb-3"
        ),
        Div(
            make_schema_table(schema),
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
            return ErrorDiv(Strong("Error: "), Span("Please enter a query"))
        
        # Start timer for query execution
        import time
        import datetime
        import json
        start_time = time.time()
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        print("About to execute query...")
        results = db.execute_query(query)
        print("Query executed, processing results...")
        
        # Calculate execution time
        execution_time = time.time() - start_time
        if "error" in results:
            print(f"Query error: {results['error']}")
            return Div(ErrorDiv(Strong("SQL Error: "), P(results["error"])), cls="single-query-result")
        
        # Limit display to 100 rows for performance
        display_data = results["data"][:100]
        total_rows = len(results["data"])
        
        if not display_data:
            print("Query returned no results")
            return Div(Strong("Query completed "), Span(f"in {execution_time:.2f}s"), P("No results returned", cls="text-sm"), cls="single-query-result")

            
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
                    make_query_results_table(results, display_data),
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
            ErrorDiv(
                Strong("Application Error: "),
                P(f"An unexpected error occurred: {str(e)}"),
                cls="my-4 single-query-result"
            )
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
    success = db.reset_connection()
    
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
            success, error = db.reset_with_new_db(str(file_path))
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

def get_database_schema_info():
    """Get comprehensive schema information for all tables to inform AI translation"""
    tables = db.get_table_names()
    schema_info = {}
    
    # Process all tables
    for table in tables:
        try:
            schema = get_table_schema(table)
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
        
        # Remove markdown code block formatting
        sql_query = sql_query.strip('`').removeprefix('sql\n').strip()
        
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
async def translate_query_endpoint(query:str):
    """Endpoint to translate natural language to SQL and automatically execute it"""
    print("==== Starting translate_query endpoint ====")
    
    try:
        # Get form data
        natural_language_query = query
        print(f"Translating natural language query: {natural_language_query[:100]}...")
        result = translate_natural_language_to_sql(natural_language_query)
        
        if "error" in result:
            print(f"Translation error: {result['error']}")
            return ErrorDiv(
                Strong("Translation Error: "),
                P(result["error"]),
            )
        
        # Get the SQL query and add the original natural language as a comment
        sql_query = f"-- Natural Language: {natural_language_query}\n\n{result['sql']}"
        print(f"Successfully translated to SQL: {sql_query[:100]}...")
        
        # Update the SQL editor with the translated query
        
        
        # Execute the query (use the actual SQL part, not the comment)
        print("Automatically executing the translated query...")
        execution_results = execute_query(result["sql"])
        
        # Generate timestamp for query history
        start_time = time.time()
        execution_time = time.time() - start_time
       
        # Display error if there was a problem executing the query
        if "error" in execution_results:
            print(f"Query execution error: {execution_results['error']}")
            return Div(ErrorDiv(Strong("SQL Error: "), P(execution_results["error"])))
        
        # Process results similar to run_query function
        # Limit display to 100 rows for performance
        display_data = execution_results["data"][:100]
        total_rows = len(execution_results["data"])
        
        if not display_data:
            print("Query returned no results")
            return Div(
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
            Div(
                Div(
                    Strong("Query successful "),
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
                    make_query_results_table(execution_results, display_data),
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
            Strong("Application Error: "),
            P(f"An unexpected error occurred: {str(e)}", 
              cls="mt-2 font-mono text-sm p-3 bg-red-100 rounded overflow-x-auto"),
            cls=TextT.error)


def make_json_cell(value: str, column_name: str) -> Td:
    """Create a table cell for JSON data with prettify and explore options"""
    return Td(
        Div(
            Div(
                Span(truncate_text(value, 50), cls="json-text"),
                Span("JSON", cls="json-badge"),
                cls="cursor-pointer",
                onclick=f"toggleJsonPrettify(this)"),
            Div(cls="json-prettified", style="display: none;"),
            Button(
                "Explore JSON",
                cls="mt-2 text-xs bg-blue-50 text-blue-600 px-2 py-1 rounded border border-blue-200 hover:bg-blue-100",
                onclick=f"openJsonExplorer({json.dumps(value)}, '{column_name}')"),
            data_json=value,
            cls="json-cell p-2"),
        )

def make_query_results_table(results: dict, display_data: list) -> Table:
    """Create a table component for query results using MonsterUI Table"""
    def cell_render(key: str, value: Any) -> Td:
        value_str = str(value)
        return make_json_cell(value_str, key) if is_json(value_str) else Td(value_str)
    
    return TableFromDicts(
        header_data=results["columns"],
        body_data=[dict(zip(results["columns"], row)) for row in display_data],
        body_cell_render=cell_render,)

def make_schema_table(schema: list) -> Table:
    """Create a table component for schema display using MonsterUI Table"""    
    def cell_render(key: str, value: Any) -> Td:
        match key.lower():
            case "column name": return Td(value)
            case "type": return Td(value,)
            case "nullable":
                is_nullable = value == "Yes"
                return Td(value, cls=f"{'text-green-600' if is_nullable else 'text-red-600'}")
    
    body_data = [
        {"Column Name": col[0], "Type": col[1], "Nullable": "Yes" if col[3] else "No"}
        for col in schema]
    
    return TableFromDicts(header_data=["Column Name", "Type", "Nullable"], 
                          body_data=body_data,
                          body_cell_render=cell_render,
                          )

if __name__ == "__main__":
    # Register cleanup function to run on exit
    atexit.register(cleanup_resources)
    serve() 