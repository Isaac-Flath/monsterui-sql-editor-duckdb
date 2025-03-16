#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI components for DuckDB SQL Editor using MonsterUI
"""

from fasthtml.common import *
from monsterui.all import *

def create_navbar(current_db_path):
    """Create the navigation bar"""
    return Div(
        Div(
            H1("DuckDB SQL Editor", cls="text-xl font-bold"),
            P(f"Connected to: {current_db_path}", cls=TextPresets.muted_sm, id="db-path-display"),
            cls="flex flex-col"
        ),
        Div(
            Button("Change Database", 
                   cls="btn btn-sm btn-outline", 
                   onclick="openDatabaseModal()"),
            Button("Reset Connection", 
                   cls="btn btn-sm btn-outline ml-2", 
                   hx_get="/reset-connection", 
                   hx_target="#reset-result"),
            cls="flex items-center"
        ),
        cls="flex justify-between items-center p-4 bg-base-200 rounded-lg mb-4"
    )

def create_sidebar(tables):
    """Create the sidebar with table list"""
    table_items = []
    for table in tables:
        table_items.append(
            Div(
                Div(
                    Span(table, cls="font-medium"),
                    cls="flex-1"
                ),
                Button(
                    UkIcon("chevron-down"),
                    cls="btn btn-ghost btn-xs",
                    hx_get=f"/table/{table}",
                    hx_target=f"#schema-{table}",
                    hx_trigger="click",
                    onclick=f"toggleSchema('{table}')"
                ),
                cls="table-item flex items-center justify-between p-2 hover:bg-base-200 rounded cursor-pointer",
                id=f"table-item-{table}"
            )
        )
        # Add schema container (initially empty)
        table_items.append(
            Div(
                id=f"schema-{table}",
                cls="schema-container"
            )
        )
    
    return Card(
        CardHeader(
            H3("Tables", cls="card-title"),
            P(f"{len(tables)} tables found", cls=TextPresets.muted_sm)
        ),
        CardBody(
            Div(
                *table_items,
                cls="table-list divide-y"
            ) if tables else P("No tables found", cls=TextPresets.muted_sm),
            cls="p-0"
        ),
        cls="sidebar h-full"
    )

def create_query_editor():
    """Create the SQL query editor"""
    return Card(
        CardHeader(
            H3("SQL Query", cls="card-title"),
            Div(
                Label(
                    Input(type="checkbox", cls="toggle toggle-sm mr-2", id="mode-toggle", onchange="toggleEditorMode()"),
                    Span("Natural Language", cls="mode-label", id="nl-mode-label"),
                    cls="cursor-pointer flex items-center"
                ),
                cls="flex items-center"
            ),
            cls="flex justify-between items-center"
        ),
        CardBody(
            Form(
                Div(
                    Div(
                        Div(id="line-numbers", cls="line-numbers"),
                        Textarea(
                            id="sql-editor",
                            cls="sql-editor with-line-numbers",
                            placeholder="Enter SQL query here...",
                            name="query"
                        ),
                        cls="editor-wrapper"
                    ),
                    cls="query-container"
                ),
                Div(
                    Button(
                        "Run Query",
                        type="submit",
                        cls="btn btn-primary",
                        hx_post="/execute-query",
                        hx_target="#query-results",
                        hx_indicator="#query-spinner"
                    ),
                    Button(
                        "Translate to SQL",
                        type="button",
                        cls="translate-btn ml-2",
                        hx_post="/translate-query",
                        hx_target="#sql-editor",
                        hx_indicator="#translate-spinner"
                    ),
                    Div(
                        Loading(LoadingT.spinner + LoadingT.sm, id="query-spinner"),
                        cls="ml-2"
                    ),
                    Div(
                        Loading(LoadingT.spinner + LoadingT.sm, id="translate-spinner"),
                        cls="ml-2"
                    ),
                    cls="flex items-center mt-4"
                ),
                id="query-form",
                cls="w-full"
            )
        ),
        cls="mb-4"
    )

def create_results_area():
    """Create the results area"""
    return Card(
        CardHeader(
            H3("Results", cls="card-title"),
            Div(
                Div(id="query-tabs", cls="query-tabs"),
                cls="flex-1 overflow-x-auto"
            ),
            cls="flex items-center"
        ),
        CardBody(
            Div(
                id="query-results",
                cls="min-h-[200px]"
            ),
            cls="p-0"
        ),
        cls="result-container"
    )

def create_database_modal():
    """Create the database connection modal"""
    return Div(
        Div(id="modal-backdrop", cls="hidden"),
        Div(
            Div(
                Div(
                    H3("Connect to a DuckDB Database", cls="text-lg font-semibold"),
                    Button("×", cls="btn btn-ghost btn-sm", onclick="closeDatabaseModal()"),
                    cls="flex justify-between items-center p-4 border-b"
                ),
                Div(
                    Form(
                        Div(
                            Label("Choose File:", for_="db_file", cls="block mb-1 font-medium"),
                            Input(
                                type="file",
                                id="db_file",
                                name="db_file",
                                accept=".duckdb,.db",
                                cls="file-input file-input-bordered w-full"
                            ),
                            cls="form-control mb-4"
                        ),
                        Div(
                            Button(
                                "Connect",
                                type="submit",
                                cls="btn btn-primary",
                                hx_post="/change-database",
                                hx_target="#result-area",
                                hx_encoding="multipart/form-data"
                            ),
                            cls="flex justify-end"
                        ),
                        id="upload-form"
                    ),
                    Div(id="result-area"),
                    cls="p-4"
                ),
                cls="bg-base-100 rounded-lg shadow-lg w-full max-w-md"
            ),
            id="database-modal",
            cls="hidden"
        )
    )

def create_table_schema_component(table_name, schema):
    """Create a component to display table schema"""
    columns = []
    for col in schema:
        columns.append(
            Div(
                Div(col["name"], cls="column-name"),
                Div(col["type"], cls="column-type"),
                Div(
                    Span("✓" if col["notnull"] else "✗"),
                    cls="column-nullable"
                ),
                cls="schema-column-item"
            )
        )
    
    return Div(
        Div(
            Div(
                Span("Columns", cls="font-medium"),
                Span(f"{len(schema)} total", cls="column-count"),
                cls="schema-summary"
            ),
            Div(
                Div(
                    Div("Name", cls="column-name"),
                    Div("Type", cls="column-type"),
                    Div("Not Null", cls="column-nullable"),
                    cls="schema-column-header"
                ),
                *columns,
                cls="schema-columns"
            ),
            cls="schema-content"
        ),
        cls="schema-container open",
        id=f"schema-{table_name}"
    )

def format_query_results(result):
    """Format query results as a table"""
    if result.get("error"):
        return Alert(result["error"], cls=AlertT.error)
    
    if not result["columns"] or not result["data"]:
        return Alert("Query executed successfully, but returned no data.", cls=AlertT.info)
    
    # Create table header
    header_cells = [Th(col) for col in result["columns"]]
    header = Tr(*header_cells)
    
    # Create table rows
    rows = []
    for row_data in result["data"]:
        cells = []
        for col in result["columns"]:
            value = row_data.get(col, "")
            if value is None:
                cells.append(Td("NULL", cls="text-gray-400 italic"))
            elif isinstance(value, (dict, list)):
                cells.append(Td(
                    Button(
                        "View JSON",
                        cls="btn btn-xs btn-outline",
                        onclick=f"showJsonViewer('{json.dumps(value)}')"
                    )
                ))
            else:
                cells.append(Td(str(value)))
        rows.append(Tr(*cells))
    
    return Div(
        Div(
            Table(
                Thead(header),
                Tbody(*rows),
                cls="result-table"
            ),
            cls="table-wrapper"
        ),
        P(f"Returned {len(result['data'])} rows", cls="text-xs text-gray-500 mt-2 px-4 pb-2")
    ) 