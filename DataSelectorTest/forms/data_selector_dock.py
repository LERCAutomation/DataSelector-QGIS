from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDockWidget, QFileDialog, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy, QWidget, QVBoxLayout, QMessageBox
from qgis.core import QgsMessageLog, Qgis

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

        # Call the parent constructor
        super().__init__(parent)
        self.setupUi(self)

        # Set the on_close callback to None
        self._on_close_callback = None

        # Load config from XML
        self.config = DataSelectorConfig()
        if not self.config.loaded:
            self.labelMessage.setText("Failed to load config file.")
        else:
            self.labelMessage.setText("")

        # Connect to SQL Server
        self.db = SQLServerFunctions(self.config.sde_file)

        # Set up the UI components
        self.checkClearLog.setChecked(self.config.clear_log)
        self.checkOpenLog.setChecked(self.config.open_log)
        
        # Populate table list on load
        if self.config.loaded:
            self.refresh_tables()

        # Define a translation map from display names to internal format codes
        self.format_translation = {
            "Shapefile": "shp",
            "CSV file (comma delimited)": "csv",
            "Text file (tab delimited)": "txt"
        }

        # Define a reverse map for display names
        self.format_map = {
            'csv': 'CSV file (comma delimited)',
            'txt': 'Text file (tab delimited)',
            'shp': 'Shapefile'
        }

        # Translate config value if it matches one of the short codes
        display_format = self.format_map.get(self.config.default_format.lower(), self.config.default_format)

        # Set the output format default in the combo box
        index = self.comboOutputFormat.findText(display_format)
        if index != -1:
            self.comboOutputFormat.setCurrentIndex(index)
        else:
            self.comboOutputFormat.setCurrentIndex(0)

        # Connect signal to changes in the table name selection
        self.comboTableName.currentIndexChanged.connect(self.handle_table_selection)

        # Clear tooltip for the Columns text box
        self.textColumns.setToolTip("")

        # Connect button signals
        self.buttonClear.clicked.connect(self.clear_form)
        self.buttonLoad.clicked.connect(self.load_query)
        self.buttonSave.clicked.connect(self.save_query)
        self.buttonVerify.clicked.connect(self.verify_sql)
        self.buttonRun.clicked.connect(self.run_query)
        self.buttonRefreshTables.clicked.connect(self.refresh_tables)

        # Hook up logic
        self.textColumns.mouseDoubleClickEvent = self.load_columns

    def set_on_close_callback(self, callback):
        """Allow the plugin to reset its reference when closed."""
        self._on_close_callback = callback

    def closeEvent(self, event):
        if self._on_close_callback:
            self._on_close_callback()
        event.accept()

    def refresh_tables(self):
        """Fetch filtered table names from SQL Server and populate dropdown."""

        # Clear existing items
        self.comboTableName.clear()
        # Add default item
        self.comboTableName.addItem("Select a table")
        # Reset to default index
        self.comboTableName.setCurrentIndex(0)

        # Set the wildcard filters, schema, and objects table
        include_wc = self.config.include_wildcard
        exclude_wc = self.config.exclude_wildcard
        schema = self.config.schema
        objects_table = self.config.objects_table

        # Fetch table names from SQL Server
        tables = self.db.get_table_names(objects_table, include_wc, exclude_wc, schema)

        # Add the tables to the dropdown
        self.comboTableName.addItems(tables)

        # Check if any tables were found
        if not tables:
            self.labelMessage.setText("No tables found in SQL Server")
            return

    def load_columns(self, event):
        """Load field names from selected table and populate Columns box."""

        table = self.comboTableName.currentText()
        if not table:
            return

        columns = self.db.get_columns(table)
        if self.config.columns_vertical:
            self.textColumns.setPlainText(",\n".join(columns))
        else:
            self.textColumns.setPlainText(", ".join(columns))

        # write_log(self.log_file, f"Loaded columns for table: {table}")

    def build_query(self):
        """Assemble the SQL query from UI components."""
        cols = self.textColumns.toPlainText().strip()
        where = self.textWhere.toPlainText().strip()
        group = self.textGroupBy.toPlainText().strip()
        order = self.textOrderBy.toPlainText().strip()
        table = self.comboTableName.currentText()

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

        # Replace any illegal characters in the user name string.
        user_id = strip_illegals(getpass.getuser())

        # Replace hyphen with underscore.
        user_id = user_id.replace("-", "_")

        # If the user ID is empty, set it to "Temp".
        if not user_id:
            user_id = "Temp"
        
        # Set up the log file path and name
        self.log_file = os.path.join(self.config.log_path, f"DataSelector_{user_id}.log")

        # Clear the log file if the checkbox is checked
        if self.checkClearLog.isChecked():
            delete_log_file(self.log_file)

        # If the userid is temp
        if user_id == "Temp":
            write_log(self.log_file, "User ID not found. User ID used will be 'Temp'")






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
        output_format = self.comboOutputFormat.currentText().lower()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Output", "", "All Files (*)")
        if not file_path:
            return

        write_log(self.log_file, f"Exporting as {output_format} to {file_path}")

        # Translate display format to internal key
        format_key = self.format_translation.get(output_format, None)

        # Dispatch table for output writers
        writer_map = {
            "shp": write_shapefile,
            "csv": write_csv,
            "txt": write_txt
        }

        # Write the output using the appropriate function
        if format_key in writer_map:
            success = writer_map[format_key](file_path, headers, rows)
        else:
            success = False

        # Check if the clear stored procedure is defined
        if self.config.clear_proc:
            write_log(self.log_file, "Deleting temporary tables ...")
            if not self.db.run_procedure(self.config.clear_proc):
                self.labelMessage.setText("Error: Deleting the temporary tables.")
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

        # write_log(self.log_file, f"Validating SQL: {sql}")

        is_valid = self.db.validate_sql(sql, timeout=self.config.sql_timeout)
        self.labelMessage.setText("SQL is valid." if is_valid else "SQL is NOT valid.")

        # write_log(self.log_file, "SQL validated successfully" if is_valid else "SQL failed validation")

    def save_query(self):
        """Save the current query parts to a .qsf file."""

        # Set the default path for the save dialog
        default_path = self.config.query_path

        # Set the default file name based on the previous loaded query name
        query_name = self.query_name if hasattr(self, "query_name") else ""

        # Set up the file dialog
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Save Query As...")
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setDefaultSuffix("qsf")
        file_dialog.setNameFilter("Query Files (*.qsf)")

        # Set the default directory and file name
        if default_path:
            file_dialog.setDirectory(default_path)
        if query_name:
            file_dialog.selectFile(query_name)

        # Loop until a valid file name is provided
        file_path = ""
        while True:
            if file_dialog.exec_():
                file_path = file_dialog.selectedFiles()[0]

                file_base, ext = os.path.splitext(file_path)

                # Ensure .qsf extension
                if not ext:
                    file_path = file_base + ".qsf"
                else:
                    if ext.lower() != ".qsf":
                        QMessageBox.critical(self, "DataSelector", "File name has incorrect extension. Save cancelled.")
                        return False

                break
            else:
                return False
            
        # Save the query
        try:
            # Save the query name for future saves
            self.query_name = os.path.basename(file_path)

            # Set the selected table in the combo box
            selected_table = self.comboTableName.currentText()
            if selected_table and selected_table == "Select a table":
                # No valid table selected
                selected_table = None

            # Set the selected output format in the combo box
            if self.comboOutputFormat.currentIndex() > 0:
                selected_format = self.comboOutputFormat.currentText()

            # Save the query to the file
            with open(file_path, "w", encoding="utf-8") as f:
                
                # Define a helper function to format lines
                def format_line(label, value):
                    return f"{label} {{{value.strip().replace('\n', ' ')}}}"

                # Write each part of the query to the file
                f.write(format_line("Fields", self.textColumns.toPlainText()) + "\n")
                f.write(format_line("From", selected_table or "") + "\n")
                f.write(format_line("Where", self.textWhere.toPlainText()) + "\n")
                f.write(format_line("Group By", self.textGroupBy.toPlainText()) + "\n")
                f.write(format_line("Order By", self.textOrderBy.toPlainText()) + "\n")
                f.write(format_line("Format", selected_format or "") + "\n")

            self.labelMessage.setText("Query saved.")
            return True

        except Exception as e:
            QMessageBox.critical(self, "DataSelector", f"Error saving file: {str(e)}")
            return False
    
    def load_query(self):
        """Load a saved .qsf query file into the text fields."""

        # Set the default path for the open dialog
        default_path = self.config.query_path

        # Set the default file name based on the previous loaded query name
        query_name = self.query_name if hasattr(self, "query_name") else ""

        # Set up the file dialog
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Load Query...")
        file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
        file_dialog.setDefaultSuffix("qsf")
        file_dialog.setNameFilter("Query Files (*.qsf)")
        file_dialog.setFileMode(QFileDialog.ExistingFiles)

        # Set the default directory and file name
        if default_path:
            file_dialog.setDirectory(default_path)
        if query_name:
            file_dialog.selectFile(query_name)

        selected_file = None
        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                selected_file = selected_files[0]

        # If no file was selected, return
        if not selected_file:
            return False
    
        # Clear the form
        self.textColumns.clear()
        self.textWhere.clear()
        self.textGroupBy.clear()
        self.textOrderBy.clear()

        # Set query name from file (for future saves, if applicable)
        self.query_name = os.path.splitext(os.path.basename(selected_file))[0]

        # Read and parse the .qsf file
        with open(selected_file, "r") as f:

            # Read each line and process it
            for line in f:
                # Strip whitespace and check for empty lines
                line = line.strip()
                if not line:
                    continue

                if line.upper().startswith("FIELDS {") and line.upper() != "FIELDS {}":
                    value = line[8:-1]  # strip 'FIELDS {' and '}'
                    self.textColumns.setPlainText(value.replace("$$", "\n"))
                elif line.upper().startswith("FROM {") and line.upper() != "FROM {}":
                    value = line[6:-1]  # strip 'FROM {' and '}'
                    # Find the index of the table in the combo box
                    index = self.comboTableName.findText(value)
                    # If found, set it as the current index
                    if index != -1:
                        self.comboTableName.setCurrentIndex(index)
                elif line.upper().startswith("WHERE {") and line.upper() != "WHERE {}":
                    value = line[7:-1]  # strip 'WHERE {' and '}'
                    self.textWhere.setPlainText(value.replace("$$", "\n"))
                elif line.upper().startswith("GROUP BY {") and line.upper() != "GROUP BY {}":
                    value = line[10:-1]  # strip 'GROUP BY {' and '}'
                    self.textGroupBy.setPlainText(value.replace("$$", "\n"))
                elif line.upper().startswith("ORDER BY {") and line.upper() != "ORDER BY {}":
                    value = line[10:-1]  # strip 'ORDER BY {' and '}'
                    self.textOrderBy.setPlainText(value.replace("$$", "\n"))
                elif line.upper().startswith("FORMAT {") and line.upper() != "FORMAT {}":
                    value = line[8:-1]  # strip 'FORMAT {' and '}'
                    # Find the index of the format in the combo box
                    index = self.comboOutputFormat.findText(value)
                    # If found, set it as the current index
                    if index != -1:
                        self.comboOutputFormat.setCurrentIndex(index)

        self.labelMessage.setText("Query loaded.")
        return True

    def clear_form(self):
        """Clear all query entry fields."""
        self.textColumns.clear()
        self.textWhere.clear()
        self.textGroupBy.clear()
        self.textOrderBy.clear()

        self.labelMessage.setText("Query cleared.")

    def handle_table_selection(self, index):
        """Handle changes in the selected table name."""

        # If the selected index is not 0 and the first item is still the default
        if index > 0 and self.comboTableName.itemText(0) == "Select a table":
            # Remove the default item
            self.comboTableName.removeItem(0)

            # Set tooltip for the Columns text box
            self.textColumns.setToolTip("Double-click to populate with list of columns from the selected table")
