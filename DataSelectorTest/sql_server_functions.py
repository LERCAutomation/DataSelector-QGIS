from qgis.core import QgsMessageLog, Qgis

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
            # Connect to the database using the connection string
            if not self.connection or not self._is_connection_open():
                self.connection = pyodbc.connect(self.conn_str, timeout=5)

            # Return the connection object
            return self.connection
        
        except Exception as e:
            print(f"[SQL Connect Error] {e}")
            return None

    def _is_connection_open(self):
        """
        Check if the connection is open.
        """
        try:
            # Check if there is a connection to the database
            conn = self._connect()
            if not conn:
                return False

            # Create a cursor and execute a simple query
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")

            # Close the cursor
            cursor.close()

            # Return True if the connection is open
            return True
        
        except:
            return False

    def get_table_names(self, objects_table, include_wildcard=None, exclude_wildcard=None, schema=None):
        """
        Query the configured view/table to return the list of selectable spatial tables.
        Applies wildcard filtering if provided.
        """
        try:

            # Check if there is a connection to the database
            conn = self._connect()
            if not conn:
                return []

            # Create a cursor and execute the SQL query
            cursor = conn.cursor()
            sql = f"SELECT ObjectName FROM {objects_table}"
            cursor.execute(sql)
            rows = [row[0] for row in cursor.fetchall()]

            # Apply include wildcard filtering if provided
            if include_wildcard:
                inc_pattern = fnmatch_to_regex(include_wildcard, schema)
                inc_regex = re.compile(inc_pattern, re.IGNORECASE)
                rows = [name for name in rows if inc_regex.match(name)]

            # Apply exclude wildcard filtering if provided
            if exclude_wildcard:
                exc_pattern = fnmatch_to_regex(exclude_wildcard, schema)
                exc_regex = re.compile(exc_pattern, re.IGNORECASE)
                rows = [name for name in rows if not exc_regex.match(name)]

            # Remove schema prefix from names if present
            if schema:
                rows = [name.split('.')[1] if name.startswith(schema + '.') else name for name in rows]

            # Sort the table names alphabetically and return them
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
            # Check if there is a connection to the database
            conn = self._connect()
            if not conn:
                return []

            # Create a cursor and execute the SQL query
            cursor = conn.cursor()
            sql = f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ?"
            cursor.execute(sql, table_name)

            # Fetch all column names, filtering out 'shape' and 'sp_geometry' (case-insensitive) and return them
            return [
                row[0] for row in cursor.fetchall()
                if row[0].lower() not in ('shape', 'sp_geometry', 'mi_style')
            ]

        except Exception as e:
            QgsMessageLog.logMessage(f"[Get Columns Error] {e}", "DataSelector", Qgis.Critical)
            return []

    def execute_sql(self, sql):
        """
        Execute a SQL query and return all rows.
        Used for running the final export query.
        """
        try:
            # Check if there is a connection to the database
            conn = self._connect()
            if not conn:
                return None

            # Create a cursor and execute the SQL query
            cursor = conn.cursor()
            cursor.execute(sql)

            # Fetch all rows and return them
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
            # Check if there is a connection to the database
            conn = self._connect()
            if not conn:
                return False

            # Create a cursor and execute the stored procedure
            cursor = conn.cursor()
            cursor.execute(f"EXEC {proc_name}")
            cursor.commit()

            # Return True if the procedure executed successfully
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
            # Check if there is a connection to the database
            conn = self._connect()
            if not conn:
                return False

            # Create a cursor
            cursor = conn.cursor()

            # Set the noexec option to validate the SQL
            cursor.execute("SET NOEXEC ON")

            # Execute the SQL statement
            cursor.execute(sql)

            # Clear the noexec option
            cursor.execute("SET NOEXEC OFF")

            # Return True if the SQL is valid
            return True
        
        except Exception as e:
            print(f"[SQL Validation Error] {e}")
            return False
