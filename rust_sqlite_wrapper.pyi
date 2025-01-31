# sqlite_wrapper.pyi

class Database:
    """
    A small wrapper around an SQLite database connection to perform basic operations.
    """

    def __new__(cls, db_path: str) -> "Database":
        """
        Create a new Database instance.

        Args:
            db_path (str): The path to the SQLite database file.

        Returns:
            Database: An instance of the Database class.
        """
        ...

    def execute(self, query: str) -> None:
        """
        Execute an SQL query on the database.

        Args:
            query (str): The SQL query to execute.

        Raises:
            RuntimeError: If the query execution fails.
        """
        ...
