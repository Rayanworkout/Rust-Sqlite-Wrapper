from rust_sqlite_wrapper import Database

db = Database()

db.create_table("users2", {
    "name": str,
    "age": int
})