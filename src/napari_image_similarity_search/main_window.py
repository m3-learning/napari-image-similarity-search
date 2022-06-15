from qtpy import QtWidgets as qtw
from qtpy import QtGui as qtg
from qtpy import QtCore as qtc
from .search_and_import_files import ImportData, UMAPParams
from .selected_images import OpenSelectImages
from .label_save_images import LabelSaveImages


class MainWindow(qtw.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Window")

        layout = qtw.QVBoxLayout()

        layout.setAlignment(qtc.Qt.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)

        # set header font size
        labelFont = qtg.QFont()
        labelFont.setBold(True)
        labelFont.setPointSize(9)

        self.importLabel = qtw.QLabel("Import Data")
        self.parameterLabel = qtw.QLabel("UMAP Parameters")
        self.imagesLabel = qtw.QLabel("Selecting and Labeling Images")

        self.importLabel.setFont(labelFont)
        self.parameterLabel.setFont(labelFont)
        self.imagesLabel.setFont(labelFont)

        # add widgets to main window
        layout.addWidget(self.importLabel, alignment=qtc.Qt.AlignCenter)
        layout.addWidget(ImportData(), alignment=qtc.Qt.AlignTop)
        layout.addWidget(self.parameterLabel, alignment=qtc.Qt.AlignCenter)
        layout.addWidget(UMAPParams(), alignment=qtc.Qt.AlignTop)
        layout.addWidget(self.imagesLabel, alignment=qtc.Qt.AlignCenter)
        layout.addWidget(OpenSelectImages(), alignment=qtc.Qt.AlignTop)
        layout.addWidget(LabelSaveImages(), alignment=qtc.Qt.AlignTop)

        widget = qtw.QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)
