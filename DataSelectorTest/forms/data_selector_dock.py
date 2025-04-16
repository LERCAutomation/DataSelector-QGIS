from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDockWidget, QFileDialog, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy
import os

from ..config_loader import DataSelectorConfig
from ..sql_server_functions import SQLServerFunctions
from ..file_functions import write_csv, write_txt, write_shapefile

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'data_selector_dock.ui'))


class DataSelectorDockWidget(QDockWidget, FORM_CLASS):
    def __init__(self, parent=None):
        """Initialize the dockable widget and load configuration."""
        super().__init__(parent)
        self.setupUi(self)

        # Load config from XML
        self.config = DataSelectorConfig()
        if not self.config.loaded:
            self.labelMessage.setText("Failed to load config file.")
        else:
            self.labelMessage.setText("")

        # Connect to SQL Server
        self.db = SQLServerFunctions(self.config.sde_file)

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

        # Procedure buttons
        self.buttonRunProc = QPushButton("Run Selection Procedure")
        self.buttonClearProc = QPushButton("Clear Selection Procedure")
        self.layout().addWidget(self.buttonRunProc)
        self.layout().addWidget(self.buttonClearProc)
        self.buttonRunProc.clicked.connect(self.run_selection_procedure)
        self.buttonClearProc.clicked.connect(self.clear_selection_procedure)

    def setup_button_layout(self):
        """Arrange buttons visually into a left-right horizontal layout."""
        layout = QHBoxLayout()
        layout.addWidget(self.buttonLoad)
        layout.addWidget(self.buttonSave)
        layout.addWidget(self.buttonClear)
        layout.addWidget(self.buttonVerify)
        layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout.addWidget(self.buttonRun)
        self.layout().addLayout(layout)

    def refresh_tables(self):
        """Fetch table names from SQL Server and populate dropdown."""
        self.comboTable.clear()
        tables = self.db.get_table_names(self.config.objects_table)
        self.comboTable.addItems(tables)
        self.labelMessage.setText(f"{len(tables)} tables loaded.")

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
        sql = self.build_query()
        results = self.db.execute_sql(sql)
        if not results:
            self.labelMessage.setText("No data returned or query failed.")
            return

        headers = [desc[0] for desc in self.db.connection.cursor().description]
        rows = results

        output_format = self.comboOutput.currentText().lower()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Output", "", "All Files (*)")
        if not file_path:
            return

        if output_format == "csv":
            success = write_csv(file_path, headers, rows)
        elif output_format == "txt":
            success = write_txt(file_path, headers, rows)
        elif output_format == "shp":
            success = write_shapefile(file_path, headers, rows)
        else:
            success = False

        self.labelMessage.setText("Export successful." if success else "Export failed.")

    def verify_sql(self):
        """Validate SQL using SET NOEXEC ON/OFF."""
        sql = self.build_query()
        is_valid = self.db.validate_sql(sql, timeout=self.config.sql_timeout)
        self.labelMessage.setText("SQL is valid." if is_valid else "SQL is NOT valid.")

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

    def run_selection_procedure(self):
        """Execute stored procedure to generate records."""
        if self.db.run_procedure(self.config.select_proc):
            self.labelMessage.setText("Selection procedure executed successfully.")
        else:
            self.labelMessage.setText("Failed to execute selection procedure.")

    def clear_selection_procedure(self):
        """Execute stored procedure to clear selection."""
        if self.db.run_procedure(self.config.clear_proc):
            self.labelMessage.setText("Clear procedure executed successfully.")
        else:
            self.labelMessage.setText("Failed to execute clear procedure.")
