from . import widget_definitions as wd
from qtpy import QtWidgets as qtw
import numpy as np
from PIL import Image
import os
import re
import sys


# appends image paths from files to a list to use in UMAP creation
class SearchFiles(qtw.QFileDialog):
    """appends image paths from selected user files to a list to use in UMAP creation"""

    images = []
    """list of images selected by user from files in viewable form"""
    imgpaths = []
    """list of file paths to selected image files"""
    img_arrays = []
    """list of selected images in ndarray form"""
    img_coords_dict = {}
    """dictionary of images and their respective coordinates from UMAP embedding"""
    img_width = 0
    """The width of all images selected for viewing. Image width must be same for all images; ImageResizeWarning() is 
    called if all images are not of same size."""

    def __init__(self):
        super().__init__()

        self.setVisible(False)

        # only selects files
        self.setFileMode(qtw.QFileDialog.DirectoryOnly)
        self.setOption(qtw.QFileDialog.DontUseNativeDialog, True)

        list_view = self.findChild(qtw.QListView, 'listView')
        tree_view = self.findChild(qtw.QTreeView)

        # allow user to multi-select files
        if list_view:
            list_view.setSelectionMode(qtw.QAbstractItemView.ExtendedSelection)

        if tree_view:
            tree_view.setSelectionMode(qtw.QAbstractItemView.ExtendedSelection)

        # append image file paths to list
        if self.exec_():
            fpaths = []
            selectfolders = self.selectedFiles()
            for f in selectfolders:
                for directory, root, files in os.walk(f):
                    for file in files:
                        fpaths.append(os.path.join(directory, file))

            # converts images to numpy array
            for imgpath in fpaths:
                # napari compliant image formats
                if imgpath.endswith('.png') or imgpath.endswith('.jpg') or imgpath.endswith('.jpeg'):
                    SearchFiles.imgpaths.append(imgpath)
                    image = Image.open(imgpath).convert("RGB")

                    # check if image is square
                    if image.size[0] == image.size[1]:
                        SearchFiles.img_width = image.size[0]

                    else:
                        # find smallest dimension of non-square image and resize to square shape
                        if image.size[0] <= image.size[1]:
                            SearchFiles.img_width = image.size[0]
                        else:
                            SearchFiles.img_width = image.size[1]

                        image = image.resize((SearchFiles.img_width, SearchFiles.img_width))

                    SearchFiles.images.append(image)
                    img_array = np.asarray(image)
                    SearchFiles.img_arrays.append(img_array)

                else:
                    pass

            if all(x.size == SearchFiles.img_arrays[0].shape for x in SearchFiles.img_arrays):
                pass
            else:
                self.dialog = ImageResizeWarning()
                self.dialog.show()

            SearchFiles.img_coords_dict['images'] = SearchFiles.imgpaths

            self.setVisible(False)

class ImageResizeWarning(qtw.QMessageBox):
    """Message box that warns users that selected images do not have the same dimensions and will be resized unless
    user chooses to restart plugin with new image with all same dimensions"""

    irw_img_width = 0
    """the average image width of all chosen images and the width that all image dimensions will be resized to"""

    def __init__(self):
        super(ImageResizeWarning, self).__init__()

        self.layout = qtw.QVBoxLayout()
        self.setText("All images selected are not of the same size and will be resized to average image "
                     "width, unless new images of equal dimensions are supplied.")
        self.setWindowTitle("Required Images Resize Warning")

        self.setStandardButtons(qtw.QMessageBox.Ok | qtw.QMessageBox.Cancel)

        btn_value = self.exec()
        if btn_value == qtw.QMessageBox.Ok:
            # calculate average width of all images selected
            sf_img_arrays = SearchFiles.img_arrays
            avg_width = np.floor(np.sum(img_array.shape[0] for img_array in sf_img_arrays) / len(sf_img_arrays))

            ImageResizeWarning.irw_img_width = int(avg_width)

            # apply average width as the new dimension for each image
            for i, image in enumerate(SearchFiles.images):
                resized_image = image.resize((ImageResizeWarning.irw_img_width, ImageResizeWarning.irw_img_width))
                img_array = np.asarray(resized_image)
                SearchFiles.img_arrays[i] = img_array

            self.setVisible(False)

        # exit gui if user rejects resizing
        else:
            sys.exit(0)


def get_image_coords():
    """retrieves data about selected user images including the images paths, sizes, and arrays

    Returns
    -------
    sf_img_coords_dict : dict
        dictionary of images and their UMAP embedding coordinates from SearchFiles() class
    img_dim : int
        dimension of all images selected
    sf_img_arrays : list of ndarrays
        list of the ndarray format of images selected from SearchFiles() class

    """
    sf_img_coords_dict = SearchFiles.img_coords_dict
    sf_img_arrays = SearchFiles.img_arrays
    sf_img_width = SearchFiles.img_width
    irw_img_width = ImageResizeWarning.irw_img_width
    if irw_img_width == 0:  # add irw. back if needed
        img_dim = sf_img_width
    else:
        img_dim = irw_img_width

    return sf_img_coords_dict, img_dim, sf_img_arrays


class UMAPParams(qtw.QWidget):
    scaled_coords = []
    params_dict = {}

    def __init__(self):
        super(UMAPParams, self).__init__()

        self.layout = qtw.QHBoxLayout()

        # line to enter UMAP parameters
        self.paramslineedit = qtw.QLineEdit(self)
        self.paramslineedit.setPlaceholderText("Enter Parameter(s)")
        self.paramslineedit.setMinimumWidth(200)

        # confirmation button for UMAP parameters
        self.paramsbtn = qtw.QPushButton(self)
        self.paramsbtn.setText("Load UMAP")
        self.paramsbtn.setMaximumWidth(150)
        self.paramsbtn.clicked.connect(self.load_UMAP)

        self.layout.addWidget(self.paramslineedit)
        self.layout.addWidget(self.paramsbtn)
        self.layout.setContentsMargins(0, 0, 0, 30)
        self.setLayout(self.layout)

    def load_UMAP(self):
        # list of user parameters
        params_list = str(self.paramslineedit.text()).split(", ")

        params_dict = {}
        # separate input UMAP parameters
        for param in params_list:
            param = re.split(r"=", param)
            # convert string params to integers
            if param[1].isdigit():
                i = int(param[1])
                params_dict[param[0]] = i

            else:
                params_dict[param[0]] = param[1]

        # get data from SearchFiles and ImageResizeWarning classes
        img_coords_dict, img_width, _ = get_image_coords()

        # generate UMAP from selected files and parameters
        x, y = wd.get_UMAP(SearchFiles.img_arrays, params_dict)
        UMAP_points = wd.get_points(x, y)
        x_coord_max, x_coord_min, y_coord_max, y_coord_min, x_coords, y_coords = wd.find_coordinates(
            UMAP_points)
        len_of_array, scale_factor = wd.scale_distance(UMAP_points, img_width)
        scaled_coordinates = wd.rescale_points(x_coord_max, x_coord_min, y_coord_max, y_coord_min, len_of_array,
                                               x_coords, y_coords, scale_factor)
        # split array to get coordinates for each image
        split_scaled_coords = np.vsplit(scaled_coordinates, len(scaled_coordinates))
        img_coords_dict['coords'] = split_scaled_coords
        wd.view_UMAP(scaled_coordinates, SearchFiles.img_arrays)

        # update scaled_coords to include new coordinates
        UMAPParams.scaled_coords = scaled_coordinates

        # update params_dict to include new parameters dictionary
        UMAPParams.params_dict = params_dict


# button to open SearchFiles
class ImportData(qtw.QWidget):
    def __init__(self):
        super(ImportData, self).__init__()
        self.layout = qtw.QHBoxLayout()

        self.btn = qtw.QPushButton("Import Image Data Folder(s)")
        self.btn.clicked.connect(self.get_files)

        self.layout.addWidget(self.btn)
        self.layout.setContentsMargins(0, 0, 0, 30)
        self.setLayout(self.layout)

    def get_files(self):
        SearchFiles().setVisible(True)
