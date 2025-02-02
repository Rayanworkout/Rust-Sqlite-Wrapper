import unittest
import os

from rust_sqlite_wrapper import Database

class TestRustSQLiteWrapper(unittest.TestCase):

    TEST_DB_NAME = "./test_db.sqlite"

    def __init__(self, methodName = "runTest"):
        super().__init__(methodName)
        if os.path.exists(TestRustSQLiteWrapper.TEST_DB_NAME):
            print("Deleting existing test database.")
            os.remove(TestRustSQLiteWrapper.TEST_DB_NAME)

    def setUp(self):
        """Initialize a fresh database instance before each test."""
        self.db = Database(TestRustSQLiteWrapper.TEST_DB_NAME)

    def tearDown(self):
        """Close the database connection after each test."""
        self.db.close()

    def test_create_table(self):
        """Test creating a table."""
        try:
            self.db.create_table("users", {
            "name": str,
            "age": int,
            "is_underage": bool
        })
        except Exception as e:
            self.fail(f"An error occurred while creating the table: {e}")

    def test_insert_and_query_data(self):
        """Test inserting and retrieving data."""
        self.db.create_table("users", {
            "name": str,
            "age": int,
            "is_underage": bool
        })

        q = "INSERT INTO users (name, age, is_underage) VALUES (?, ?, ?)"
        result = self.db.execute(q, ("rayan", 27, False))
        self.assertEqual(result, 1)

        # result = self.db.execute("SELECT * FROM users", [])
        # self.assertEqual(result, [("rayan", 25, 1)])  # SQLite stores bool as 1/0

    # def test_multiple_insertions(self):
    #     """Test inserting multiple rows."""
    #     self.db.create_table("users", {
    #         "name": str,
    #         "age": int,
    #         "new": bool
    #     })

    #     data = [
    #         ("Alice", 30, False),
    #         ("Bob", 22, True),
    #         ("Charlie", 40, False)
    #     ]
    #     for entry in data:
    #         self.db.execute("INSERT INTO users (name, age, new) VALUES (?, ?, ?)", entry)

    #     result = self.db.execute("SELECT * FROM users ORDER BY age")
    #     self.assertEqual(result, [
    #         ("Bob", 22, 1),
    #         ("Alice", 30, 0),
    #         ("Charlie", 40, 0)
    #     ])

    # def test_invalid_data_insertion(self):
    #     """Test handling of invalid data type insertions."""
    #     self.db.create_table("users", {
    #         "name": str,
    #         "age": int,
    #         "new": bool
    #     })

    #     with self.assertRaises(Exception):  # Adjust based on actual exception raised
    #         self.db.execute("INSERT INTO users (name, age, new) VALUES (?, ?, ?)", ("Eve", "not_an_int", True))

    # def test_table_does_not_exist(self):
    #     """Test querying a non-existing table."""
    #     with self.assertRaises(Exception):  # Adjust based on actual exception
    #         self.db.execute("SELECT * FROM non_existing_table")

    # def test_close_database(self):
    #     """Test closing the database and ensuring further operations fail."""
    #     self.db.create_table("users", {
    #         "name": str,
    #         "age": int,
    #         "new": bool
    #     })
    #     self.db.close()
    #     with self.assertRaises(Exception):  # Adjust based on actual exception
    #         self.db.execute("SELECT * FROM users")

if __name__ == '__main__':
    unittest.main()
