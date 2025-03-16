#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Helper utilities for DuckDB SQL Editor
"""

import json
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def is_json(value):
    """Check if a value is valid JSON"""
    if not isinstance(value, str):
        return False
    try:
        json.loads(value)
        return True
    except ValueError:
        return False

def truncate_text(text, max_length=100):
    """Truncate text to a maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def get_database_schema_info():
    """Get schema information for all tables in the database"""
    from .db import get_table_names, get_table_schema
    
    schema_info = []
    tables = get_table_names()
    
    for table in tables:
        columns = get_table_schema(table)
        schema_info.append({
            "table_name": table,
            "columns": columns
        })
    
    return schema_info

def format_for_openai(schema_info):
    """Format database schema information for OpenAI API"""
    formatted_schema = []
    
    for table in schema_info:
        table_name = table["table_name"]
        columns = table["columns"]
        
        column_descriptions = []
        for col in columns:
            column_descriptions.append(f"{col['name']} ({col['type']})")
        
        formatted_schema.append(f"Table: {table_name}\nColumns: {', '.join(column_descriptions)}")
    
    return "\n\n".join(formatted_schema)

def translate_natural_language_to_sql(natural_language_query):
    """Translate natural language query to SQL using OpenAI API"""
    from .db import get_table_names, get_table_schema
    
    # Get OpenAI API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "OpenAI API key not found in environment variables", "sql": ""}
    
    # Get database schema information
    schema_info = get_database_schema_info()
    formatted_schema = format_for_openai(schema_info)
    
    # Prepare the prompt
    system_prompt = """You are a helpful SQL assistant that translates natural language queries into SQL for DuckDB.
Given the database schema below, generate a SQL query that answers the user's question.
Only return the SQL query without any explanation or markdown formatting.
"""
    
    user_prompt = f"""Database Schema:
{formatted_schema}

Natural Language Query: {natural_language_query}

SQL Query:"""
    
    # Call OpenAI API
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 500
            },
            timeout=10
        )
        
        response.raise_for_status()
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            sql_query = result["choices"][0]["message"]["content"].strip()
            return {"error": None, "sql": sql_query}
        else:
            return {"error": "No response from OpenAI API", "sql": ""}
    
    except requests.exceptions.RequestException as e:
        return {"error": f"Error calling OpenAI API: {str(e)}", "sql": ""}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}", "sql": ""} 