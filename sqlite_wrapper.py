import os
import sqlite3

from threading import Lock
from typing import Any, List, Tuple


class Database:
    """
    Classe de base pour facilement interagir avec une base de données SQLite.

    Cette classe sert de couche d'abstraction pour effectuer des opérations sur
    la base de données, telles que la création de tables, l'insertion de lignes
    et l'exécution de requêtes. Elle implémente un modèle de singleton pour
    éviter les problèmes de parallélisme des requêtes en permettant une seule
    instance de connexion à la base de données.

    Il est possible d'hériter de cette classe afin d'utiliser ses
    méthodes tout en ajoutant d'autres méthodes.

    Méthodes :
        __new__(cls):
            Garantit qu'une seule instance de la classe est créée (singleton).

        __init__(db_name: str = "db.sqlite3"):
            Initialise la connexion à la base de données en utilisant le nom
            du fichier de base de données fourni.

        close():
            Ferme la connexion à la base de données SQLite.

        execute_query(query, params=None) -> Tuple[bool, int, int]:
            Exécute une requête SQL et renvoie un tuple contenant le statut de
            succès, le nombre de lignes affectées et l'ID de la dernière ligne
            insérée.

        fetch_all(query, params=None):
            Exécute une requête SELECT et récupère toutes les lignes résultantes.

        fetch_one(query, params=None):
            Exécute une requête SELECT et récupère une seule ligne résultante.

        create_table(table_name: str, columns: dict) -> Tuple[bool, int, int]:
            Crée une table avec le nom et les colonnes spécifiés.

        insert_row(table_name, data):
            Insère une ligne dans la table spécifiée avec les données fournies.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        """
        Crée une instance unique de la classe (Singleton).

        Cette méthode garantit qu'une seule instance de la base de données
        sera utilisée à travers l'application.

        Retourne :
            Une instance unique de la classe MigrationDatabase.
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
            db_name (str) : Nom du fichier de base de données SQLite (par défaut "db.sqlite").
        """

        script_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(script_dir, db_name)

        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.connection.cursor()

    def close(self):
        """
        Ferme la connexion à la base de données SQLite.

        Cette méthode doit être appelée pour libérer les ressources une fois que
        les opérations sur la base de données sont terminées.
        """
        if self.connection:
            self.connection.close()

    def execute_query(self, query, params=None) -> Tuple[bool, int, int]:
        """
        Exécute une requête SQL.

        Arguments :
            query (str) : La requête SQL à exécuter.
            params (tuple) : Les paramètres optionnels à inclure dans la requête (par défaut None).

        Retourne :
            Tuple[bool, int, int] : Un tuple contenant :
                - bool : Indique si la requête a été exécutée avec succès.
                - int : Nombre de lignes affectées par la requête.
                - int : ID de la dernière ligne insérée (si applicable).
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.connection.commit()

            return True, self.cursor.rowcount, self.cursor.lastrowid

        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            return False, self.cursor.rowcount, self.cursor.lastrowid

    def fetch_all(self, query, params=None) -> List[Any]:
        """
        Récupère toutes les lignes d'une requête SELECT.

        Arguments :
            query (str) : La requête SQL SELECT.
            params (tuple) : Les paramètres optionnels pour la requête (par défaut None).

        Retourne :
            list : Une liste contenant toutes les lignes résultantes de la requête.
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            return []

    def fetch_one(self, query, params=None):
        """Récupère une seule ligne d'une requête SELECT.

        Arguments :
            query (str) : La requête SQL SELECT.
            params (tuple) : Les paramètres optionnels pour la requête (par défaut None).

        Retourne :
            tuple : La première ligne résultante de la requête ou None en cas d'erreur.
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            return None

    def create_table(self, table_name: str, columns: dict) -> Tuple[bool, int, int]:
        """
        Crée une table dans la base de données.

        Arguments :
            table_name (str) : Le nom de la table à créer.
            columns (dict) : Dictionnaire contenant les noms de colonnes en tant que clés
                            et leurs types de données en tant que valeurs.

        Retourne :
            Tuple[bool, int, int] : Indique si la table a été créée avec succès.
        """
        columns_str = ", ".join(f"{col} {dtype}" for col, dtype in columns.items())
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})"

        return self.execute_query(query)

    def insert_row(self, table_name, data):
        """
        Insère une ligne dans une table.

        Arguments :
            table_name (str) : Le nom de la table dans laquelle insérer les données.
            data (dict) : Dictionnaire contenant les noms de colonnes en tant que clés
                        et les valeurs correspondantes à insérer.

        Retourne :
            Tuple[bool, int, int] : Indique si l'insertion a été réalisée avec succès.
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        self.execute_query(query, tuple(data.values()))