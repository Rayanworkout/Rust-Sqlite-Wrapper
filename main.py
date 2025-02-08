from rust_sqlite_wrapper import Database

db = Database("./database.sqlite")

db.create_table("users", {"name": str, "age": int, "is_underage": bool})

# Quickly insert data

# Executing a raw query
r = db.fetch_all(
    "SELECT * FROM users", []
)
