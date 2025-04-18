from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDockWidget, QFileDialog, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy, QWidget, QVBoxLayout
import os
import getpass

from ..config_loader import DataSelectorConfig
from ..sql_server_functions import SQLServerFunctions
from ..file_functions import write_csv, write_txt, write_shapefile, create_log_file, write_log, delete_log_file, open_log_file
from ..string_functions import strip_illegals

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'data_selector_dock.ui'))

class DataSelectorDockWidget(QDockWidget, FORM_CLASS):
    def __init__(self, parent=None):
        """Initialize the dockable widget and load configuration."""
        super().__init__(parent)
        self.setupUi(self)

        self._on_close_callback = None

        # Load config from XML
        self.config = DataSelectorConfig()
        if not self.config.loaded:
            self.labelMessage.setText("Failed to load config file.")
        else:
            self.labelMessage.setText("")

        # Connect to SQL Server
        self.db = SQLServerFunctions(self.config.sde_file)

        user_id = strip_illegals(getpass.getuser())
        if not user_id:
            user_id = "Temp"
        self.log_file = os.path.join(self.config.log_path, f"DataSelector_{user_id}.log")
        self.checkClearLog.setChecked(self.config.clear_log)
        self.checkOpenLog.setChecked(self.config.open_log)
        if self.checkClearLog.isChecked():
            delete_log_file(self.log_file)
        create_log_file(self.log_file)
        if user_id == "Temp":
            write_log(self.log_file, "User ID not found. User ID used will be 'Temp'")

        # Populate table list on load
        if self.config.loaded:
            self.refresh_tables()

        # Hook up logic
        self.textColumns.mouseDoubleClickEvent = self.load_columns

        # Layout: place buttons at bottom in order
        self.setup_button_layout()

        # Connect signals
        self.buttonClear.clicked.connect(self.clear_form)
        self.buttonLoad.clicked.connect(self.load_query)
        self.buttonSave.clicked.connect(self.save_query)
        self.buttonVerify.clicked.connect(self.verify_sql)
        self.buttonRun.clicked.connect(self.run_query)
        self.buttonRefreshTables.clicked.connect(self.refresh_tables)

    def set_on_close_callback(self, callback):
        """Allow the plugin to reset its reference when closed."""
        self._on_close_callback = callback

    def closeEvent(self, event):
        if self._on_close_callback:
            self._on_close_callback()
        event.accept()

    def setup_button_layout(self):
        """Arrange buttons visually into a left-right horizontal layout at the bottom."""
        layout = QHBoxLayout()
        layout.addWidget(self.buttonLoad)
        layout.addWidget(self.buttonSave)
        layout.addWidget(self.buttonClear)
        layout.addWidget(self.buttonVerify)
        layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout.addWidget(self.buttonRun)

        # Wrap the layout in a QWidget (because we can't insert QLayout directly)
        layout_wrapper = QWidget()
        layout_wrapper.setLayout(layout)

        # Add it to the main layout at the end
        self.findChild(QVBoxLayout, "verticalLayout").addWidget(layout_wrapper)

    def refresh_tables(self):
        """Fetch filtered table names from SQL Server and populate dropdown."""
        self.comboTable.clear()

        include_wc = self.config.include_wildcard
        exclude_wc = self.config.exclude_wildcard
        schema = self.config.schema
        objects_table = self.config.objects_table

        tables = self.db.get_table_names(objects_table, include_wc, exclude_wc, schema)
        self.comboTable.addItems(tables)
        self.labelMessage.setText(f"{len(tables)} tables loaded.")

        write_log(self.log_file, f"Refreshed table list: {len(tables)} tables found")

    def load_columns(self, event):
        """Load field names from selected table and populate Columns box."""
        table = self.comboTable.currentText()
        if not table:
            return

        columns = self.db.get_columns(table)
        if self.config.columns_vertical:
            self.textColumns.setPlainText(",\n".join(columns))
        else:
            self.textColumns.setPlainText(", ".join(columns))

        write_log(self.log_file, f"Loaded columns for table: {table}")

    def build_query(self):
        """Assemble the SQL query from UI components."""
        cols = self.textColumns.toPlainText().strip()
        where = self.textWhere.toPlainText().strip()
        group = self.textGroupBy.toPlainText().strip()
        order = self.textOrderBy.toPlainText().strip()
        table = self.comboTable.currentText()

        sql = f"SELECT {cols or '*'} FROM {table}"
        if where:
            sql += f" WHERE {where}"
        if group:
            sql += f" GROUP BY {group}"
        if order:
            sql += f" ORDER BY {order}"
        return sql

    def run_query(self):
        """Execute SQL query and export results."""

        write_log(self.log_file, "Running selection stored procedure")

        # Check if the run stored procedure is defined
        if self.config.select_proc:
            # Run selection stored procedure first
            if not self.db.run_procedure(self.config.select_proc):
                self.labelMessage.setText("Failed to run selection procedure.")
                write_log(self.log_file, "Failed to run selection stored procedure")
                return

        # Build and execute the SQL query
        sql = self.build_query()
        write_log(self.log_file, f"Executing SQL: {sql}")
        results = self.db.execute_sql(sql)
        if not results:
            self.labelMessage.setText("No data returned or query failed.")
            write_log(self.log_file, "SQL returned no data or failed")
            return

        # Extract the column names from the SQL Server result set metadata
        headers = [desc[0] for desc in self.db.connection.cursor().description]

        # Assign the actual query result rows (list of tuples) to 'rows'
        rows = results

        # Prompt user for output file name
        output_format = self.comboOutput.currentText().lower()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Output", "", "All Files (*)")
        if not file_path:
            return

        write_log(self.log_file, f"Exporting as {output_format} to {file_path}")

        # Create the output file of the selected format from the query results
        if output_format == "csv":
            success = write_csv(file_path, headers, rows)
        elif output_format == "txt":
            success = write_txt(file_path, headers, rows)
        elif output_format == "shp":
            success = write_shapefile(file_path, headers, rows)
        else:
            success = False

        # Clear selection afterward
        # Check if the clear stored procedure is defined
        if self.config.clear_proc:
            write_log(self.log_file, "Running clear selection stored procedure")
            if not self.db.run_procedure(self.config.clear_proc):
                self.labelMessage.setText("Failed to run clear procedure.")
                return

        # Show success message
        self.labelMessage.setText("Export successful." if success else "Export failed.")
        write_log(self.log_file, "Export complete" if success else "Export failed")

        if self.checkOpenLog.isChecked():
            write_log(self.log_file, "Opening log file")
            open_log_file(self.log_file)

    def verify_sql(self):
        """Validate SQL using SET NOEXEC ON/OFF."""
        sql = self.build_query()
        write_log(self.log_file, f"Validating SQL: {sql}")
        is_valid = self.db.validate_sql(sql, timeout=self.config.sql_timeout)
        self.labelMessage.setText("SQL is valid." if is_valid else "SQL is NOT valid.")
        write_log(self.log_file, "SQL validated successfully" if is_valid else "SQL failed validation")

    def save_query(self):
        """Save the current query parts to a .qsf file."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Query", "", "Query Files (*.qsf)")
        if file_path:
            with open(file_path, "w") as f:
                f.write(self.textColumns.toPlainText().strip() + "\n")
                f.write(self.textWhere.toPlainText().strip() + "\n")
                f.write(self.textGroupBy.toPlainText().strip() + "\n")
                f.write(self.textOrderBy.toPlainText().strip() + "\n")
            self.labelMessage.setText("Query saved.")

    def load_query(self):
        """Load a saved .qsf query file into the text fields."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Query", "", "Query Files (*.qsf)")
        if file_path:
            with open(file_path, "r") as f:
                lines = f.readlines()
            if len(lines) >= 4:
                self.textColumns.setPlainText(lines[0].strip())
                self.textWhere.setPlainText(lines[1].strip())
                self.textGroupBy.setPlainText(lines[2].strip())
                self.textOrderBy.setPlainText(lines[3].strip())
                self.labelMessage.setText("Query loaded.")

    def clear_form(self):
        """Clear all query entry fields."""
        self.textColumns.clear()
        self.textWhere.clear()
        self.textGroupBy.clear()
        self.textOrderBy.clear()
        self.labelMessage.setText("Query cleared.")
