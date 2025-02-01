from rust_sqlite_wrapper import Database

db = Database()

db.create_table("users", {
    "Name": str,
    "age": int,
    "new": bool
})

q = "insert into users (name, age, new) values (?, ?, ?)"


db.execute(q, ("rayan", (False,), 2))

# Closing the database connection is a good practice
db.close()