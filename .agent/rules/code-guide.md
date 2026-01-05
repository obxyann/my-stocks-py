---
trigger: always_on
---

## Project Overview
- Language: Python
- Libraries: pandas
- Database: SQLite
- UI: Tkinter ttk
- Data visualization: seaborn + mplcursors

## Code Style
- Follow PEP 8
- Prefer explicit code over clever code
- Avoid overly compact one-liners if readability is reduced
- Use early return to reduce nesting when appropriate

## Naming Conventions

- Case Style: Use `snake_case` for all symbols (variables, functions, methods, modules)
- Classes: Use `PascalCase` for class names
- Constants: Use `UPPER_SNAKE_CASE` for constant values

## Commenting & Documentation

- Language: Always use English
- Style: Be concise; omit unnecessary words like 'the', 'a', 'an'
- In-line Comments: Start with a lowercase letter and end without a period
- Docstrings:
  * Use Google Style Docstrings
  * Start with an uppercase letter and end without a period

## Function Design
- Each function should do one thing
- Keep functions small and focused
- Avoid side effects unless explicitly stated in function description
- No business logic inside database access functions

## Database (SQLite Usage)

- Engine: Use `sqlite3` standard library
- Schema: Refer to `docs/DB-Schema.txt` for table structures
- Architecture:
   * Basic logic resides in `database/stock.py`, which provides database operations
   * Maintenance tasks are handled by `db_manager.py` (CLI tool)
- Safety: Always use context managers (`with` statements) for database connections and cursors to ensure they are closed properly
- Security: Use parameterized queries to prevent SQL injection

## Data Processing (Pandas Usage)
- Avoid chained assignment
- Prefer vectorized operations over loops
- Do not modify input DataFrame in-place unless clearly documented
- Column names must follow database naming conventions

## About Error Handling
- Catch specific exceptions, avoid bare except
- Do not silently ignore errors
- Raise exceptions with meaningful messages

## Project Structure
- Do not introduce new files or modules unless explicitly requested
- Respect existing module responsibilities
- Database basic logic must stay in `database/stock.py`