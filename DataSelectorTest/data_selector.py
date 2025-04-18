from qgis.PyQt.QtWidgets import QAction
from .forms.data_selector_dock import DataSelectorDockWidget

class DataSelector:
    def __init__(self, iface):
        """Plugin entry point."""
        self.iface = iface
        self.dock_widget = None
        self.action = None

    def initGui(self):
        # Create an action for the Plugins menu
        self.action = QAction("Open DataSelector", self.iface.mainWindow())
        self.action.triggered.connect(self.toggle_dock)

        # Add it to the Plugins menu
        self.iface.addPluginToMenu("&DataSelector", self.action)

        # Load and show the dock widget when the plugin is started
        self.dock_widget = DataSelectorDockWidget()
        self.dock_widget.set_on_close_callback(self.on_dock_closed)
        self.iface.addDockWidget(0, self.dock_widget)

    def unload(self):
        # Remove from Plugins menu
        self.iface.removePluginMenu("&DataSelector", self.action)

        # Unload and remove the dock widget when the plugin is stopped
        if self.dock_widget:
            self.iface.removeDockWidget(self.dock_widget)
            self.dock_widget = None

    def toggle_dock(self):
        if self.dock_widget is None:
            # Re-create if it's been closed
            self.dock_widget = DataSelectorDockWidget()
            self.dock_widget.set_on_close_callback(self.on_dock_closed)
            self.iface.addDockWidget(0, self.dock_widget)
        else:
            # If it's hidden, show it
            if not self.dock_widget.isVisible():
                self.dock_widget.show()
                self.dock_widget.raise_()
                self.dock_widget.activateWindow()

    def on_dock_closed(self):
        self.dock_widget = None
