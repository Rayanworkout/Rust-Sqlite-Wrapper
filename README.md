## Rust SQLite Wrapper

A simple utility library to easily interact with a SQLite database. This library uses [Pyo3](https://pyo3.rs/v0.15.1/), Rust bindings for Python.

### Installation

### Usage

```python
from rust_sqlite_wrapper import Database

# Create a database
db = Database("database.sqlite")

# Create a table using Python's builtin types
db.create_table("users", {"name": str, "age": int, "is_underage": bool})

# Quickly insert data
db.insert(table="users", values={"name": "rayan", "is_underage": False, "age": "27"})

# Or alternatively execute a raw query
db.execute(
    "INSERT INTO users (name, is_underage, age) VALUES (?, ?, ?)", ("rayan", False, 27)
)

# fetchone() and fetchall() methods


```