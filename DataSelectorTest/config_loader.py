import os
import xml.etree.ElementTree as ET

class DataSelectorConfig:
    """
    This class loads and parses the XML configuration file for the DataSelector plugin.
    It stores all values as accessible attributes, using sensible defaults for optional fields.
    """

    def __init__(self):
        self.loaded = False
        self._xml_path = os.path.join(os.path.dirname(__file__), "DataSelector.xml")
        self._defaults()      # Set all properties to their default values
        self._load_xml()      # Try to load and parse the XML file

    def _defaults(self):
        """Define fallback values for all config attributes."""
        self.log_path = ""
        self.sql_connection = ""
        self.select_proc = ""
        self.clear_proc = ""
        self.extract_path = ""
        self.query_path = ""
        self.default_format = ""
        self.schema = ""
        self.objects_table = ""
        self.include_wildcard = ""
        self.exclude_wildcard = ""
        self.layer_location = ""
        self.clear_log = False
        self.open_log = False
        self.validate_sql = False
        self.sql_timeout = 30
        self.columns_vertical = False

    def _load_xml(self):
        """
        Parse the XML file and populate config fields.
        Handles missing/invalid values gracefully.
        """
        if not os.path.exists(self._xml_path):
            return

        try:
            # Parse the XML and locate the root <DataSelector> element
            tree = ET.parse(self._xml_path)
            root = tree.getroot().find("DataSelector")

            # Mandatory settings
            self.log_path = root.findtext("LogFilePath", "")
            self.sql_connection = root.findtext("SQLConnection", "")
            self.select_proc = root.findtext("SelectStoredProcedure", "")
            self.clear_proc = root.findtext("ClearStoredProcedure", "")
            self.extract_path = root.findtext("DefaultExtractPath", "")
            self.query_path = root.findtext("DefaultQueryPath", "")
            self.default_format = root.findtext("DefaultFormat", "")
            self.schema = root.findtext("DatabaseSchema", "")
            self.objects_table = root.findtext("ObjectsTable", "")
            self.include_wildcard = root.findtext("IncludeWildcard", "")
            self.exclude_wildcard = root.findtext("ExcludeWildcard", "")
            self.layer_location = root.findtext("LayerLocation", "")

            # Boolean flags — 'Yes' or 'Y' (case-insensitive) is interpreted as True
            self.clear_log = root.findtext("DefaultClearLogFile", "No").lower() in ("yes", "y")
            self.open_log = root.findtext("DefaultOpenLogFile", "No").lower() in ("yes", "y")
            self.validate_sql = root.findtext("ValidateSQL", "No").lower() in ("yes", "y")
            self.columns_vertical = root.findtext("LoadColumnsVertically", "No").lower() in ("yes", "y")

            # SQL timeout — convert from string to integer safely
            timeout_text = root.findtext("SQLTimeout", "30")
            try:
                self.sql_timeout = int(timeout_text)
            except ValueError:
                self.sql_timeout = 30

            self.loaded = True

        except Exception as e:
            print(f"[Config Error] Could not load DataSelector.xml: {e}")
            self.loaded = False
