from . import widget_definitions as wd
from . import search_and_import_files as si
from .selected_images import SelectedImages, OpenSelectImages
from qtpy import QtWidgets as qtw
from qtpy import QtGui as qtg
from qtpy import QtCore as qtc
import numpy as np
from PIL import Image


random_colors = []
# assigns image groups a unique color for their bounding boxes
def randomize_color():
    r = np.random.randint(256) / 255
    g = np.random.randint(256) / 255
    b = np.random.randint(256) / 255
    random_color = [r, g, b, 1]

    while random_color not in random_colors:
        random_colors.append(random_color)

    return random_color


# add by image width to get corners of photos to create bounding box
def make_bbox(new_coord):
    _, img_width, _ = si.get_image_coords()
    minr = new_coord[0]
    minc = new_coord[1] + img_width
    maxr = new_coord[0] + img_width
    maxc = new_coord[1]
    bbox_rects = np.array(
        [[minr, minc], [maxr, minc], [maxr, maxc], [minr, maxc]]
    )
    return bbox_rects


# widget to label and save images into labeled groups
class LabelSaveImages(qtw.QWidget):
    list_imgs = []
    bboxes = []
    imageGroups = {}

    def __init__(self):
        super().__init__()

        self.viewer = wd.viewer

        self.layout = qtw.QVBoxLayout()
        self.layout.setAlignment(qtc.Qt.AlignTop)

        self.sublayout1 = qtw.QHBoxLayout()
        self.sublayout2 = qtw.QHBoxLayout()

        # widget to enter labels for images
        self.LabelImages = qtw.QLineEdit(self)
        self.LabelImages.setPlaceholderText("Label Selected Image(s)")
        self.LabelImages.setMinimumWidth(175)

        # confirmation button for selected images
        self.SaveImages = qtw.QPushButton(self)
        self.SaveImages.setText("Confirm Image(s) Label")
        self.SaveImages.setMaximumWidth(150)
        self.SaveImages.clicked.connect(self.create_image_groups)

        # a table that lists the labels and number of images with the label
        self.LabelList = qtw.QTableWidget(self)
        self.LabelList.setRowCount(len(self.imageGroups.keys()))
        self.LabelList.setColumnCount(3)
        self.LabelList.setHorizontalHeaderLabels([" ", "Labels", "Number of Images"])
        self.LabelList.setStyleSheet("QTableWidget{ border: 1px solid black}")

        self.LabelList.setSelectionBehavior(qtw.QAbstractItemView.SelectRows)
        self.LabelList.setSelectionMode(qtw.QAbstractItemView.SingleSelection)
        self.LabelList.cellClicked.connect(self.cell_clicked)

        # set dimensions of list of image groups and labels
        self.LabelList.verticalHeader().setVisible(False)
        self.LabelList.verticalHeader().setSectionResizeMode(qtw.QHeaderView.Fixed)
        self.LabelList.horizontalHeader().setSectionResizeMode(0, qtw.QHeaderView.Fixed)
        self.LabelList.setColumnWidth(0, 30)
        self.setMaximumHeight(400)
        self.LabelList.horizontalHeader().setSectionResizeMode(1, qtw.QHeaderView.Stretch)
        self.LabelList.horizontalHeader().setSectionResizeMode(2, qtw.QHeaderView.Stretch)
        self.LabelList.setWordWrap(True)

        labelFont = qtg.QFont()
        labelFont.setBold(True)
        labelFont.setPointSize(7)

        self.labelListTitle = qtw.QLabel("Table of Image Labels ")
        self.labelListTitle.setFont(labelFont)

        self.NewUMAP = qtw.QPushButton(self)
        self.NewUMAP.setText("Generate New UMAP")
        self.NewUMAP.setMaximumWidth(150)
        self.NewUMAP.setEnabled(False)
        self.NewUMAP.setStyleSheet("QPushButton:disabled { background-color: rgba(255, 255, 255, 0.4); "
                                   "color: rgba(255, 255, 255, 0.6);}")
        self.NewUMAP.clicked.connect(self.gen_new_UMAP)

        self.ReturnBtn = qtw.QPushButton(self)
        self.ReturnBtn.setText("Return")
        self.ReturnBtn.setMaximumWidth(150)
        self.ReturnBtn.setEnabled(False)
        self.ReturnBtn.setStyleSheet("QPushButton:disabled { background-color: rgba(255, 255, 255, 0.4); "
                                     "color: rgba(255, 255, 255, 0.6);}")
        self.ReturnBtn.clicked.connect(self.return_UMAP)

        self.sublayout1.addWidget(self.LabelImages)
        self.sublayout1.addWidget(self.SaveImages)

        self.sublayout2.addWidget(self.NewUMAP)
        self.sublayout2.addWidget(self.ReturnBtn)

        self.layout.addLayout(self.sublayout1)
        self.layout.addWidget(self.labelListTitle, alignment=qtc.Qt.AlignCenter)
        self.layout.addWidget(self.LabelList)
        self.layout.addLayout(self.sublayout2)
        self.setLayout(self.layout)

    # create dict of images and their labels
    def create_image_groups(self):
        _, img_width, _ = si.get_image_coords()

        # data from SelectedImages class
        selectedImgs = SelectedImages.selectedImgs
        all_buttons = SelectedImages.buttons
        all_buttons_names = [btn.objectName().split("\\")[-1] for btn in all_buttons]

        # disables checking same button after labeling
        for btn_name in SelectedImages.selectedImgs:
            img_name = btn_name.split("\\")[-1]
            if img_name in all_buttons_names:
                i = all_buttons_names.index(img_name)
                all_buttons[i].setEnabled(False)

        poly_imgs_coords = OpenSelectImages.polygon_imgs_coords_dict

        label = str(self.LabelImages.text())
        self.imageGroups[label] = selectedImgs[:]

        # appends labels and number of images to a list for user
        currentRowCount = self.LabelList.rowCount()

        rowtext = []
        for row in range(currentRowCount):
            item = self.LabelList.item(row, 1)  # col val change due to inclusion of col for icon colors
            text = str(item.text())
            rowtext.append(text)

        for key in self.imageGroups:
            if key in rowtext:
                pass
            else:
                self.LabelList.insertRow(currentRowCount)
                self.LabelList.setItem(currentRowCount, 1, qtw.QTableWidgetItem(key))
                self.LabelList.setItem(currentRowCount, 2, qtw.QTableWidgetItem(str(len(self.imageGroups[key]))))

                bbox_color = randomize_color()
                for i in self.imageGroups[key]:
                    if i in [k for k in poly_imgs_coords]:
                        bbox_rect = make_bbox(poly_imgs_coords[i])
                        self.bboxes = self.viewer.add_shapes(bbox_rect,
                                                             face_color='transparent',
                                                             edge_width=(img_width / 10),
                                                             edge_color=bbox_color,
                                                             name=key
                                                             )

                color_brush = qtg.QBrush(qtg.QColor.fromRgbF(bbox_color[0], bbox_color[1], bbox_color[2]))
                color_brush.setStyle(qtc.Qt.SolidPattern)
                item = qtw.QTableWidgetItem()
                item.setBackground(color_brush)
                self.LabelList.setItem(currentRowCount, 0, item)

        # resets LabelImages line edit and the images selected by the user
        self.LabelImages.clear()
        selectedImgs.clear()

    def cell_clicked(self):
        self.NewUMAP.setEnabled(True)
        rows_selected = self.LabelList.selectionModel().selectedRows()
        selected_row = rows_selected[0].row()
        row_key = self.LabelList.item(selected_row, 1).text()

        _, img_dim, _ = si.get_image_coords()

        for list_img_path in self.imageGroups[row_key]:
            list_img = Image.open(list_img_path).convert("RGB")
            list_img = list_img.resize((img_dim, img_dim))
            list_img_array = np.asarray(list_img)
            self.list_imgs.append(list_img_array)

    # generate new UMAP with selected images
    def gen_new_UMAP(self):

        _, img_width, _ = si.get_image_coords()

        params_dict = si.UMAPParams.params_dict

        self.ReturnBtn.setEnabled(True)

        self.viewer.layers.select_all()
        self.viewer.layers.remove_selected()

        new_x, new_y, new_x_y_list = wd.get_UMAP(self.list_imgs, params_dict)
        new_x_max, new_x_min, new_y_max, new_y_min = wd.find_coordinates(new_x, new_y)
        new_len_of_array, scale_factor = wd.scale_distance(new_x_y_list, img_width)
        new_scaled_coords = wd.rescale_points(new_x_max, new_x_min, new_y_max, new_y_min, new_len_of_array,
                                              new_x, new_y, scale_factor)
        wd.view_UMAP(new_scaled_coords, self.list_imgs)

    # returns user to original UMAP projection
    def return_UMAP(self):
        scaled_coords = si.UMAPParams.scaled_coords

        _, _, imgs = si.get_image_coords()

        self.NewUMAP.setEnabled(False)

        self.viewer.layers.select_all()
        self.viewer.layers.remove_selected()

        wd.view_UMAP(scaled_coords, imgs)
