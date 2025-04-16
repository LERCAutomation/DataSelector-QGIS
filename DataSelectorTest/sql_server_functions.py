import pyodbc

class SQLServerFunctions:
    def __init__(self, connection_string):
        """
        Initialize the SQLServerFunctions with a connection string.
        This replaces the ArcGIS .sde file approach.
        """
        self.conn_str = connection_string
        self.connection = None

    def _connect(self):
        """
        Create and return a connection to the SQL Server database.
        Reuses the existing connection if already open.
        """
        try:
            if not self.connection or self.connection.closed:
                self.connection = pyodbc.connect(self.conn_str, timeout=5)
            return self.connection
        except Exception as e:
            print(f"[SQL Connect Error] {e}")
            return None

    def get_table_names(self, objects_table):
        """
        Query the configured view/table to return the list of selectable spatial tables.
        Equivalent to reading from the 'ObjectsTable' node in the config.
        """
        try:
            conn = self._connect()
            if not conn:
                return []

            cursor = conn.cursor()
            sql = f"SELECT name FROM {objects_table}"
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [row[0] for row in rows]
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
