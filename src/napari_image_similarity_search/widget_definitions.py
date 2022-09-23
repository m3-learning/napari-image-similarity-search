import numpy as np
import umap.umap_ as umap
import napari

viewer = napari.Viewer()

def get_UMAP(imgs, params):
    """Generates UMAP from supplied images and parameters

    Parameters
    ----------
    imgs : list
        selected images to input into UMAP algorithm
    params : dict
        UMAP parameters to manipulate embedding

    Returns
    -------
    x : list
        list of x-coordinates of all images in UMAP
    y : list
        list of y-coordinates of all images in UMAP

    """
    x_1 = np.asarray(imgs)
    nsamples, nx, ny, nz = x_1.shape
    data = x_1.reshape((nsamples, nx * ny * nz))

    embedding_UMAP = umap.UMAP(**params).fit_transform(data)
    x = embedding_UMAP[:, 0]
    y = embedding_UMAP[:, 1]

    return x, y, embedding_UMAP

def find_coordinates(x, y):
    """Find maximum and minimum values for both x and y coordinates of images in UMAP embedding

    Parameters
    ----------
    x : list
        list of x-coordinates of all images in UMAP
    y : list
        list of y-coordinates of all images in UMAP

    """

    y_min = min(y)
    x_min = min(x)
    y_max = max(y)
    x_max = max(x)
    return x_max, x_min, y_max, y_min


# find distance between each image on the canvas and get appropriate scale factor for napari canvas
def scale_distance(points, img_width):
    """Finds distance between each image on the canvas and calculates an appropriate scale factor for optimizing the
    view of the images on the napari canvas.  Scale factor is based on distance standard deviation and image size.

    Parameters
    ----------
    points : list
        respective coordinate points of each image on the canvas from UMAP embedding
    img_width : int
        Width of of all images embedded in UMAP algorithm


    Returns
    -------
    len_of_array : int
        maximum length of canvas dimension required to properly show all images on canvas
    scale_factor : int
        factor by which distances between images are scaled to properly display on canvas

    """

    distances = []

    # finds min and max distances between points
    def dist(p0, p1):
        return (((p0[0] - p1[0]) ** 2) + ((p0[1] - p1[1]) ** 2)) ** .5

    for i in range(len(points) - 1):
        for j in range(i + 1, len(points)):
            distances += [dist(points[i], points[j])]

    dist_std = np.std(distances)
    std_width_ratio = img_width / dist_std

    if std_width_ratio >= 200:
        scale_factor = int(2.5 * img_width)

    elif 175 <= std_width_ratio < 200:
        scale_factor = int(2.25 * img_width)

    elif 150 <= std_width_ratio < 175:
        scale_factor = int(2 * img_width)

    elif 125 <= std_width_ratio < 150:
        scale_factor = int(1.75 * img_width)

    elif 100 <= std_width_ratio < 125:
        scale_factor = int(1.5 * img_width)

    elif std_width_ratio < 100:
        scale_factor = int(1.25 * img_width)

    len_of_array = int(max(distances) * scale_factor)
    return len_of_array, scale_factor


def rescale_points(old_max_x, old_min_x, old_max_y, old_min_y, len_of_array, old_x, old_y, scale_factor):
    """Redefines image coordinates for viewing on napari canvas based on new scaled distance between points

    Parameters
    ----------
    old_max_x : int
        previous maximum value of x coordinate
    old_min_x : int
        previous minimum value of x coordinate
    old_max_y : int
        previous maximum value of y coordinate
    old_min_y : int
        previous minimum value of y coordinate
    len_of_array : int
        maximum length of canvas dimension required to properly show all images on canvas
    scale_factor : int
        factor by which distances between images are scaled to properly display on canvas
    old_y : list
        previous list of y-coordinates of all images in UMAP
    old_x : list
        previous list of x-coordinates of all images in UMAP


    Returns
    -------
    scaled_coords : list
        list of all image coordinates properly scaled to be displayed on napari canvas

    """

    # new vales for min and max values of x and y
    new_max_x = len_of_array
    new_min_x = scale_factor
    new_min_y = scale_factor
    new_max_y = len_of_array

    old_range_x = (old_max_x - old_min_x)
    new_range_x = (new_max_x - new_min_x)
    old_range_y = (old_max_y - old_min_y)
    new_range_y = (new_max_y - new_min_y)

    scaled_values_y = []
    scaled_values_x = []

    # find new coordinates for each images using scaling factor
    for old_value_x in old_x:
        new_value_x = int((((old_value_x - old_min_x) * new_range_x) / old_range_x) + new_min_x)
        scaled_values_x.append(new_value_x)
    for old_value_y in old_y:
        new_value_y = int((((old_value_y - old_min_y) * new_range_y) / old_range_y) + new_min_y)
        scaled_values_y.append(new_value_y)

    # get new scaled image coordinates
    scaled_coords = np.stack((scaled_values_x, scaled_values_y), axis=1)

    return scaled_coords


def view_UMAP(scaled_coords, imgs):
    """Defines napari canvas size by new image coordinates and loads images into viewer

    Parameters
    ----------
    scaled_coords : list
        list of all image coordinates properly scaled to be displayed on napari canvas
    imgs : list
        list of all selected images

    """
    x_coord_min = min(scaled_coords[:, 0])
    x_coord_max = max(scaled_coords[:, 0])

    y_coord_min = min(scaled_coords[:, 1])
    y_coord_max = max(scaled_coords[:, 1])

    # add each images as a new layer into napari canvas
    for x0, y0, img in zip(scaled_coords[:, 0], scaled_coords[:, 1], imgs):
        viewer.add_image(data=img, translate=(x0, y0))

    # rescale canvas to best fit images
    viewer.window._qt_viewer.view.camera.rect = (x_coord_min, y_coord_min, x_coord_max, y_coord_max)
    viewer.window._qt_viewer.view.camera.aspect = 1.0
