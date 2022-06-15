from . import widget_definitions as wd
from . import search_and_import_files as si
from qtpy import QtWidgets as qtw
from qtpy import QtGui as qtg
from qtpy import QtCore as qtc
import numpy as np
import matplotlib.path as pltPath

# opens widget to select images based on user's polygon drawing
class OpenSelectImages(qtw.QWidget):
    polygon_coords = []  # list of images coordinates residing in user's drawn polygons
    polygon_imgs = []
    polygon_imgs_coords_dict = {}  # dictionary of images located in polygon and their coordinates

    def __init__(self):
        super().__init__()
        self.viewer = wd.viewer  # use same viewer
        self.scaled_coords = 0

        # widget layout
        self.layout = qtw.QVBoxLayout()

        self.open_select_img = qtw.QPushButton("Select Images from Viewer")
        self.open_select_img.setMinimumWidth(200)
        self.open_select_img.setSizePolicy(qtw.QSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Fixed))

        self.open_select_img.clicked.connect(self.open_select_images)
        self.layout.addWidget(self.open_select_img)
        self.setLayout(self.layout)

        self.open_select_img.click_counter = 0

    # obtains images in drawn polygon using their corresponding coords in viewer
    # viewer can only draw on ONE shape layer at a time
    def open_select_images(self):
        # initialize instance of classes to retrieve coordinates
        scaled_coords = si.UMAPParams.scaled_coords

        img_coords, _, _ = si.get_image_coords()

        # wait until polygon is drawn to obtain data from napari canvas
        if self.open_select_img.click_counter == 0:
            for layer in self.viewer.layers:
                layer_type = layer.as_layer_data_tuple()[2]
                # only get coordinate data from shapes layer
                if layer_type == 'shapes':
                    layer_data = np.array(layer.data)
                    layer_data = np.squeeze(layer_data)

                    if layer_data.ndim > 2:  # for selection with multiple polygons
                        for row in layer_data:
                            # checks if each images coordinates are within selected area in viewer
                            polygon_path = pltPath.Path(row)
                            contains_coords = polygon_path.contains_points(scaled_coords)
                            for i in range(len(contains_coords)):
                                if contains_coords[i]:
                                    self.polygon_coords.append(scaled_coords[i])

                    else:  # for selection with one polygon
                        # checks if each images coordinates are within selected area in viewer
                        polygon_path = pltPath.Path(layer_data)
                        contains_coords = polygon_path.contains_points(scaled_coords)
                        for i in range(len(contains_coords)):
                            # appends to list if image coordinates are in selected viewer area
                            if contains_coords[i]:
                                self.polygon_coords.append(scaled_coords[i])

                    # appends images in selected area to new dictionary with their coordinates as values
                    for coord, poly_img in zip(img_coords['coords'], img_coords['images']):
                        if coord[0][0] in [i[0] for i in self.polygon_coords] \
                                and coord[0][1] in [i[1] for i in self.polygon_coords]:
                            self.polygon_imgs.append(poly_img)
                            self.polygon_imgs_coords_dict[poly_img] = coord[0]

                        else:
                            pass

                    # opens widget to select from images in drawn polygon/ selected viewer area
                    self.dialog = SelectedImages()
                    self.dialog.show()

                    # removes drawn polygon
                    if layer_type == 'shapes':
                        self.viewer.layers.remove(layer)

            self.open_select_img.click_counter += 1

        # allows for multiple selections
        elif self.open_select_img.click_counter == 1:

            #[button.setChecked(False) for button in self.dialog.buttons]  # reset checked buttons
            self.dialog.activateWindow()
            self.dialog.show()

# widget that opens in new screen to select images from polygon
class SelectedImages(qtw.QDialog):
    buttons = []
    selectedImgs = []

    def __init__(self):
        super().__init__()
        self.layout = qtw.QVBoxLayout()

        _, img_width, _ = si.get_image_coords()

        # set Scroll Area widget dimensions based on image dimensions
        self.scrollArea = qtw.QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setVerticalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOn)
        self.scrollArea.setHorizontalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setGeometry(qtc.QRect(0, 0, int(2.5 * img_width), int(1.5 * img_width)))

        self.scrollAreaWidget = qtw.QWidget()
        self.gridlayout = qtw.QGridLayout()
        self.scrollAreaWidget.setLayout(self.gridlayout)

        for poly_img in OpenSelectImages().polygon_imgs:  # poly_imgs comes from polygon coords
            button = qtw.QPushButton(self)
            icon = qtg.QPixmap(poly_img)
            button.setIcon(qtg.QIcon(icon))
            button_size = qtc.QSize(64, 64)  # img_width was too large if images are 256x256
            button.setIconSize(button_size)
            button.resize(img_width, img_width)
            button.setCheckable(True)
            button.setObjectName(str(poly_img))
            button.clicked.connect(self.select_imgs)
            button.click_counter = 0
            self.buttons.append(button)

        # organizes and aligns buttons in scroll area properly
        a = 0
        b = 0
        for btn in self.buttons:
            self.gridlayout.addWidget(btn, a, b)
            b = b + 1
            if b % 7 == 0:
                b = 0
                a = a + 1

        self.scrollArea.setWidget(self.scrollAreaWidget)
        self.layout.addWidget(self.scrollArea)

    # appends/removes selected images to a list based on button clicks
    def select_imgs(self) -> list:
        pressedimg = self.sender()
        selectedimg = pressedimg.objectName()
        self.selectedImgs.append(selectedimg)
        pressedimg.click_counter += 1
        # removes an image that is de-selected from list
        if pressedimg.click_counter % 2 == 0:
            self.selectedImgs.remove(selectedimg)
            self.selectedImgs.remove(selectedimg)
