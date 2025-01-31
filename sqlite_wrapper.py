import os
import sqlite3
from threading import Lock
from typing import Any, List, Tuple


class Database:
    """
    Classe de base pour interagir facilement avec une base de données SQLite.

    Cette classe sert de couche d'abstraction pour effectuer des opérations sur
    la base de données, telles que la création de tables, l'insertion de lignes
    et l'exécution de requêtes. Elle implémente un modèle de singleton pour
    éviter les problèmes de parallélisme en permettant une seule instance de
    connexion à la base de données.

    Il est possible d'hériter de cette classe afin d'utiliser ses méthodes tout 
    en ajoutant d'autres méthodes.

    Méthodes :
        __new__(cls): Garantit qu'une seule instance de la classe est créée (singleton).
        __init__(db_name: str = "db.sqlite3"): Initialise la connexion à la base de données.
        close(): Ferme la connexion à la base de données SQLite.
        execute_query(query, params=None) -> Tuple[bool, int, int]: 
            Exécute une requête SQL et retourne un tuple contenant :
                - bool : Succès de la requête
                - int : Nombre de lignes affectées
                - int : ID de la dernière ligne insérée
        fetch_all(query, params=None) -> List[Any]: Exécute une requête SELECT et récupère 
            toutes les lignes résultantes.
        fetch_one(query, params=None) -> Tuple[Any] | None: Exécute une requête SELECT et 
            récupère une seule ligne résultante.
        create_table(table_name: str, columns: dict) -> Tuple[bool, int, int]: Crée une table.
        insert_row(table_name, data) -> Tuple[bool, int, int]: Insère une ligne dans une table.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        """
        Implémente le pattern Singleton.

        Retourne :
            Une instance unique de la classe Database.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Database, cls).__new__(cls)
                cls._instance._initialized = False

        return cls._instance

    def __init__(self, db_name: str = "db.sqlite") -> None:
        """
        Initialise la connexion à la base de données SQLite.

        Arguments :
            db_name (str) : Nom du fichier de base de données SQLite.
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(script_dir, db_name)

        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.connection.cursor()

    def close(self) -> None:
        """
        Ferme la connexion à la base de données SQLite.

        Cette méthode doit être appelée pour libérer les ressources.
        """
        if self.connection:
            self.connection.close()

    def execute_query(self, query: str, params: Tuple = None) -> Tuple[bool, int, int]:
        """
        Exécute une requête SQL.

        Arguments :
            query (str) : La requête SQL à exécuter.
            params (tuple) : Paramètres optionnels pour la requête.

        Retourne :
            Tuple[bool, int, int] :
                - bool : Succès de la requête.
                - int : Nombre de lignes affectées.
                - int : ID de la dernière ligne insérée.
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            self.connection.commit()
            return True, self.cursor.rowcount, self.cursor.lastrowid

        except sqlite3.Error as e:
            print(f"Une erreur est survenue : {e}")
            return False, self.cursor.rowcount, self.cursor.lastrowid

    def fetch_all(self, query: str, params: Tuple = None) -> List[Any]:
        """
        Exécute une requête SELECT et récupère toutes les lignes résultantes.

        Arguments :
            query (str) : La requête SQL SELECT.
            params (tuple) : Paramètres optionnels.

        Retourne :
            list : Liste des résultats ou une liste vide en cas d'erreur.
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            return self.cursor.fetchall()

        except sqlite3.Error as e:
            print(f"Une erreur est survenue : {e}")
            return []

    def fetch_one(self, query: str, params: Tuple = None) -> Tuple[Any] | None:
        """
        Exécute une requête SELECT et récupère une seule ligne.

        Arguments :
            query (str) : La requête SQL SELECT.
            params (tuple) : Paramètres optionnels.

        Retourne :
            tuple | None : La première ligne résultante ou None en cas d'erreur.
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            return self.cursor.fetchone()

        except sqlite3.Error as e:
            print(f"Une erreur est survenue : {e}")
            return None

    def create_table(self, table_name: str, columns: dict) -> Tuple[bool, int, int]:
        """
        Crée une table dans la base de données.

        Arguments :
            table_name (str) : Nom de la table.
            columns (dict) : Dictionnaire contenant les colonnes et leurs types.

        Retourne :
            Tuple[bool, int, int] : Indique si la création a été réussie.
        """
        columns_str = ", ".join(f"{col} {dtype}" for col, dtype in columns.items())
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})"

        return self.execute_query(query)

    def insert_row(self, table_name: str, data: dict) -> Tuple[bool, int, int]:
        """
        Insère une ligne dans une table.

        Arguments :
            table_name (str) : Nom de la table.
            data (dict) : Données à insérer sous forme de dictionnaire.

        Retourne :
            Tuple[bool, int, int] : Indique si l'insertion a été réalisée avec succès.
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        return self.execute_query(query, tuple(data.values()))
