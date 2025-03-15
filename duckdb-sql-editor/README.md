# DuckDB SQL Editor

A FastHTML-based SQL editor for DuckDB, built with MonsterUI components.

## Features

- Connect to DuckDB databases (specifically `analytics.duckdb`)
- Browse tables and their schemas
- Execute SQL queries with an interactive editor
- View query results in a formatted table
- Modern UI with MonsterUI components

## Installation

This project uses Poetry for dependency management. Make sure you have Python 3.10+ and Poetry installed.

```bash
# Clone the repository
git clone <repository-url>
cd duckdb-sql-editor

# Install dependencies
poetry install
```

## Configuration

Create a `.env` file in the project root with the following variables:

```
# Path to your DuckDB database file
DUCKDB_PATH=../path/to/analytics.duckdb

# Server configuration
HOST=127.0.0.1
PORT=5001
```

## Usage

To run the application:

```bash
# Activate the Poetry virtual environment
poetry shell

# Run the application
python app.py
```

Then open your browser and navigate to http://127.0.0.1:5001.

## Technologies Used

- [Python 3.10+](https://www.python.org/)
- [FastHTML](https://www.fastht.ml/) - Modern web framework in pure Python
- [MonsterUI](https://github.com/AnswerDotAI/MonsterUI) - UI component library for FastHTML
- [DuckDB](https://duckdb.org/) - Embeddable SQL OLAP database
- [Poetry](https://python-poetry.org/) - Dependency management

## License

MIT 