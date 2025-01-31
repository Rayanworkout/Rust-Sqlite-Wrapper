from rust_sqlite_wrapper import Database

db = Database(db_path="my_db.sqlite3")

q = "CREATE TABLE IF NOT EXISTS USER (id INTEGER PRIMARY KEY);"

db.execute(q)
