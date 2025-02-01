from rust_sqlite_wrapper import Database

db = Database()

db.create_table("users4", {
    "name": str,
    "age": int,
    "new": bool
})

# Closing the database connection is a good practice
db.close()