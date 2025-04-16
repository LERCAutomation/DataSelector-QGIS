from .forms.data_selector_dock import DataSelectorDockWidget

class DataSelector:
    def __init__(self, iface):
        self.iface = iface
        self.dock_widget = None

    def initGui(self):
        self.dock_widget = DataSelectorDockWidget()
        self.iface.addDockWidget(0, self.dock_widget)

    def unload(self):
        if self.dock_widget:
            self.iface.removeDockWidget(self.dock_widget)