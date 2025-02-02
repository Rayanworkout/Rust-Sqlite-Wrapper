from rust_sqlite_wrapper import Database

db = Database("./database.sqlite")

db.create_table("users", {
    "name": str,
    "age": int,
    "is_underage": bool
})

db.insert(table="users", values={"name": "eddy", "is_underage": [True], "age": 25})