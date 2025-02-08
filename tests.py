import unittest
import os

from rust_sqlite_wrapper import Database

class TestRustSQLiteWrapper(unittest.TestCase):

    # py -m unittest .\tests.py
    TEST_DB_NAME = "test_db.sqlite"

    def __init__(self, methodName = "runTest"):
        super().__init__(methodName)
        if os.path.exists(TestRustSQLiteWrapper.TEST_DB_NAME):
            os.remove(TestRustSQLiteWrapper.TEST_DB_NAME)

    @classmethod
    def tearDownClass(cls):
        """Remove the test database after all tests."""
        if os.path.exists(TestRustSQLiteWrapper.TEST_DB_NAME):
            os.remove(TestRustSQLiteWrapper.TEST_DB_NAME)

    def setUp(self):
        """Initialize a fresh database instance before each test."""
        self.db = Database(TestRustSQLiteWrapper.TEST_DB_NAME)

    def tearDown(self):
        """Close the database connection after each test."""
        self.db.close()

    ################################################################

    ##### EXECUTE_RAW_QUERY #####
    
    def test_execute_raw_query(self):
        """Test executing a raw SQL query."""
        try:
            q = "CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT)"
            self.db.execute_raw_query(q, [])
        except Exception as e:
            self.fail(f"An error occurred while executing the raw query: {e}")

    def test_execute_raw_query_wrong_params_type(self):
        with self.assertRaises(RuntimeError):
            self.db.execute_raw_query("INSERT INTO users (name, age, is_underage) VALUES (?,?,?)", "wrong type")

    ##### END EXECUTE_RAW_QUERY #####

    ##### INSERT #####

    def test_insert_values(self):
        self.db.create_table("users", {
            "name": str,
            "age": int,
            "new": bool
        })

    ##### END INSERT #####

    ##### GLOBAL #####

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

    def test_table_does_not_exist(self):
        """Test querying a non-existing table."""
        with self.assertRaises(RuntimeError):
            self.db.execute_raw_query("SELECT * FROM non_existing_table", [])


if __name__ == '__main__':
    unittest.main()
