#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DuckDB SQL Editor with FastHTML and MonsterUI
"""

import os
import json
import tempfile
from pathlib import Path
from fasthtml.common import *
from monsterui.all import *

# Import our modules
from utils import (
    get_connection, reset_with_new_db, reset_connection,
    get_table_names, get_table_schema, execute_query,
    is_json, truncate_text, translate_natural_language_to_sql
)

from components import (
    create_navbar, create_sidebar, create_query_editor,
    create_results_area, create_database_modal,
    create_table_schema_component, format_query_results
)

# Initialize the app with MonsterUI theme
app, rt = fast_app(hdrs=Theme.blue.headers())

@rt('/')
def index():
    """Main page with SQL editor"""
    # Get current database path
    db_path = os.getenv("DUCKDB_PATH", "../duckdb-demo.duckdb")
    
    # Get table names
    tables = get_table_names()
    print(f"Loaded {len(tables)} tables from database")
    
    # Create the main layout
    return Titled("DuckDB SQL Editor", 
        # Add metadata for better styling
        Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        
        # Add CSS and JS
        Link(rel="stylesheet", href="/static/css/app.css"),
        Script(src="/static/js/app.js"),
        
        # Main container
        Container(
            # Navbar
            create_navbar(db_path),
            
            # Main content
            Div(
                # Sidebar with tables
                create_sidebar(tables),
                
                # Main content area
                Div(
                    # Query editor
                    create_query_editor(),
                    
                    # Results area
                    create_results_area(),
                    
                    cls="main-content"
                ),
                
                cls="flex gap-4"
            ),
            
            # Database modal
            create_database_modal(),
            
            # Hidden container for query results
            Div(id="hidden-results-container", style="display: none;"),
            
            # Reset result container
            Div(id="reset-result", cls="mt-4"),
            
            cls="container mx-auto px-4 py-6"
        )
    )

@rt('/table/{table_name}')
def table_info(table_name):
    """Get table schema information"""
    schema = get_table_schema(table_name)
    return create_table_schema_component(table_name, schema)

@rt('/execute-query', methods=['POST'])
async def run_query(request):
    """Execute a SQL query and return the results"""
    form = await request.form()
    query = form.get('query', '').strip()
    
    if not query:
        return Alert("Please enter a SQL query", cls=AlertT.warning)
    
    # Execute the query
    result = execute_query(query)
    
    # Add JavaScript to create a query tab
    return Div(
        format_query_results(result),
        Script(f"createQueryTab({json.dumps(query)});")
    )

@rt('/translate-query', methods=['POST'])
async def translate_query_endpoint(request):
    """Translate natural language to SQL"""
    form = await request.form()
    natural_language_query = form.get('query', '').strip()
    
    if not natural_language_query:
        return Alert("Please enter a natural language query", cls=AlertT.warning)
    
    # Translate the query
    result = translate_natural_language_to_sql(natural_language_query)
    
    if result.get("error"):
        return Alert(result["error"], cls=AlertT.error)
    
    # Return the SQL query
    return result["sql"]

@rt('/reset-connection', methods=['GET'])
async def reset_connection_endpoint(request):
    """Reset the database connection"""
    try:
        reset_connection()
        return Alert("Database connection reset successfully", cls=AlertT.success)
    except Exception as e:
        return Alert(f"Error resetting connection: {e}", cls=AlertT.error)

@rt('/change-database', methods=['POST'])
async def change_database_endpoint(request):
    """Change the database file"""
    form = await request.form()
    file = form.get('db_file')
    
    if not file:
        return Alert("Please select a database file", cls=AlertT.warning)
    
    try:
        # Create a temporary file to store the uploaded database
        with tempfile.NamedTemporaryFile(delete=False, suffix='.duckdb') as temp_file:
            temp_file.write(await file.read())
            temp_path = temp_file.name
        
        # Reset the connection with the new database
        reset_with_new_db(temp_path)
        
        # Return success message with redirect script
        return Div(
            Alert(f"Connected to new database successfully", cls=AlertT.success),
            Script("setTimeout(function() { window.location.href = '/'; }, 1500);")
        )
    except Exception as e:
        return Alert(f"Error changing database: {e}", cls=AlertT.error)

@rt('/debug', methods=['GET', 'POST'])
async def debug(request):
    """Debug endpoint for testing"""
    tables = get_table_names()
    schema_info = []
    
    for table in tables:
        schema = get_table_schema(table)
        schema_info.append({
            "table": table,
            "schema": schema
        })
    
    return Div(
        H1("Debug Information"),
        H2("Tables"),
        P(f"Found {len(tables)} tables"),
        Pre(json.dumps(schema_info, indent=2)),
        cls="p-4"
    )

if __name__ == "__main__":
    serve() 