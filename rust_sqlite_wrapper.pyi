
from typing import Dict


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


    def create_table(self, table_name: str, dict_columns: Dict[str, type]) -> None:
        """
        Creates a new table in the SQLite database.

        Args:
            table_name (str): The name of the table to be created.
            dict_columns (Dict[str, type]): A dictionary where keys are column names 
                and values are Python types (str, int, float, bool) representing the column types.

        Raises:
            RuntimeError: If a column type is not one of the allowed built-in Python types 
                (str, int, float, bool).
            Exception: If an internal SQLite error occurs.
        """
        ...

    
    def execute(self, query: str, params: tuple | list) -> None:
        """
        Execute an SQL query on the database.

        Args:
            query (str): The SQL query to execute.
            params (tuple | list): The parameters to pass to the query.

        Raises:
            RuntimeError: If the query execution fails.
        """
        ...
