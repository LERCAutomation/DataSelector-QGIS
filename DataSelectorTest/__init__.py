# This file is required for QGIS to recognize the plugin package.
# It defines the `classFactory()` method that QGIS calls when loading the plugin.

from .data_selector import DataSelector

def classFactory(iface):
    """
    QGIS calls this function when the plugin is loaded.
    
    Parameters:
        iface: The QGIS interface object, providing access to the QGIS GUI.

    Returns:
        An instance of the main plugin class (DataSelector).
    """
    return DataSelector(iface)
