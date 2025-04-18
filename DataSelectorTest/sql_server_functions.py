import pyodbc
import re

from .string_functions import fnmatch_to_regex

class SQLServerFunctions:
    def __init__(self, connection_string):
        """
        Initialize the SQLServerFunctions with a connection string.
        """
        self.conn_str = connection_string
        self.connection = None

    def _connect(self):
        """
        Create and return a connection to the SQL Server database.
        Reuses the existing connection if already open.
        """
        try:
            if not self.connection or not self._is_connection_open():
                self.connection = pyodbc.connect(self.conn_str, timeout=5)
            return self.connection
        except Exception as e:
            print(f"[SQL Connect Error] {e}")
            return None

    def _is_connection_open(self):
        """
        Check if the connection is open.
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except:
            return False

    def get_table_names(self, objects_table, include_wildcard=None, exclude_wildcard=None, schema=None):
        """
        Query the configured view/table to return the list of selectable spatial tables.
        Applies wildcard filtering if provided.
        """
        try:
            conn = self._connect()
            if not conn:
                return []

            cursor = conn.cursor()
            sql = f"SELECT ObjectName FROM {objects_table}"
            cursor.execute(sql)
            rows = [row[0] for row in cursor.fetchall()]

            if include_wildcard:
                inc_pattern = fnmatch_to_regex(include_wildcard, schema)
                inc_regex = re.compile(inc_pattern, re.IGNORECASE)
                rows = [name for name in rows if inc_regex.match(name)]

            if exclude_wildcard:
                exc_pattern = fnmatch_to_regex(exclude_wildcard, schema)
                exc_regex = re.compile(exc_pattern, re.IGNORECASE)
                rows = [name for name in rows if not exc_regex.match(name)]

            return sorted(rows)

        except Exception as e:
            print(f"[Get Tables Error] {e}")
            return []

    def get_columns(self, table_name):
        """
        Retrieve column names for a given table using the INFORMATION_SCHEMA.COLUMNS view.
        Used to populate the Columns box on double-click.
        """
        try:
            conn = self._connect()
            if not conn:
                return []

            cursor = conn.cursor()
            sql = f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ?"
            cursor.execute(sql, table_name)
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"[Get Columns Error] {e}")
            return []

    def execute_sql(self, sql):
        """
        Execute a SQL query and return all rows.
        Used for running the final export query.
        """
        try:
            conn = self._connect()
            if not conn:
                return None

            cursor = conn.cursor()
            cursor.execute(sql)
            return cursor.fetchall()
        except Exception as e:
            print(f"[SQL Execution Error] {e}")
            return None

    def run_procedure(self, proc_name):
        """
        Execute a stored procedure by name.
        Used for 'SelectStoredProcedure' and 'ClearStoredProcedure'.
        """
        try:
            conn = self._connect()
            if not conn:
                return False

            cursor = conn.cursor()
            cursor.execute(f"EXEC {proc_name}")
            cursor.commit()
            return True
        except Exception as e:
            print(f"[Procedure Error] {e}")
            return False

    def validate_sql(self, sql, timeout=10):
        """
        Validate SQL syntax without running the query using SET NOEXEC ON/OFF.
        This mimics the ArcGIS add-in logic used for query validation.
        """
        try:
            conn = self._connect()
            if not conn:
                return False

            cursor = conn.cursor()
            cursor.execute("SET NOEXEC ON")
            cursor.execute(sql)
            cursor.execute("SET NOEXEC OFF")
            return True
        except Exception as e:
            print(f"[SQL Validation Error] {e}")
            return False
