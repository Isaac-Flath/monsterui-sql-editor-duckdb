"""
Utilities for DuckDB SQL Editor
"""

from .db import (
    get_connection,
    reset_with_new_db,
    reset_connection,
    get_table_names,
    get_table_schema,
    execute_query,
    cleanup_resources
)

from .helpers import (
    is_json,
    truncate_text,
    get_database_schema_info,
    format_for_openai,
    translate_natural_language_to_sql
)

__all__ = [
    'get_connection',
    'reset_with_new_db',
    'reset_connection',
    'get_table_names',
    'get_table_schema',
    'execute_query',
    'cleanup_resources',
    'is_json',
    'truncate_text',
    'get_database_schema_info',
    'format_for_openai',
    'translate_natural_language_to_sql'
] 