# DuckDB SQL Editor

A modern SQL editor for DuckDB databases built with FastHTML and MonsterUI.

## Features

- Connect to DuckDB databases
- Browse tables and their schemas
- Execute SQL queries
- Translate natural language to SQL using OpenAI
- View query results in a tabular format
- JSON viewer for complex data types
- Query history tabs

## Project Structure

```
duckdb-sql-editor/
├── app.py                 # Main application file
├── components/            # UI components
│   ├── __init__.py
│   └── ui.py              # UI component definitions
├── static/                # Static assets
│   ├── css/
│   │   └── app.css        # Custom CSS styles
│   └── js/
│       └── app.js         # JavaScript functions
└── utils/                 # Utility functions
    ├── __init__.py
    ├── db.py              # Database operations
    └── helpers.py         # Helper functions
```

## Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install fasthtml monsterui duckdb python-dotenv
```

3. Set up environment variables (optional):

```bash
# Create a .env file
echo "DUCKDB_PATH=/path/to/your/database.duckdb" > .env
echo "OPENAI_API_KEY=your_openai_api_key" >> .env
```

## Usage

1. Run the application:

```bash
python app.py
```

2. Open your browser and navigate to `http://localhost:8000`

## Development

The application is built with:

- [FastHTML](https://fasthtml.answer.ai/) - A Python library for building HTML applications
- [MonsterUI](https://monsterui.answer.ai/) - A UI component library for FastHTML
- [DuckDB](https://duckdb.org/) - An in-process SQL OLAP database management system

## License

MIT 