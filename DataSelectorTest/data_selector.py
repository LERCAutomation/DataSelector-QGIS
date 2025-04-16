from .forms.data_selector_dock import DataSelectorDockWidget

class DataSelector:
    def __init__(self, iface):
        """Plugin entry point."""
        self.iface = iface
        self.dock_widget = None

    def initGui(self):
        """Load and show the dock widget when the plugin is started."""
        self.dock_widget = DataSelectorDockWidget()
        self.iface.addDockWidget(0, self.dock_widget)

    def unload(self):
        """Unload and remove the dock widget when the plugin is stopped."""
        if self.dock_widget:
            self.iface.removeDockWidget(self.dock_widget)
