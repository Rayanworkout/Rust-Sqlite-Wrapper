
class Database:
    """
    A small wrapper around an SQLite database connection to perform basic operations.
    """

    def __new__(cls, db_path: str) -> "Database":
        """
        Create a new Database instance.

        Args:
            db_path (str): The path to the SQLite database file.
            It should end with one of these extensions:
            `.sqlite` `.sql` `.db`

        Returns:
            Database: An instance of the Database class.
        """
        ...


    def create_table(self, table_name: str, column_names: list[str]):
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
