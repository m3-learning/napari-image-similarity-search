import numpy as np
import umap.umap_ as umap
import matplotlib.pyplot as plt
import napari

viewer = napari.Viewer()

# creating graph with images and retrieving points
def get_UMAP(imgs, params):
    x_1 = np.asarray(imgs)  # convert images to array
    nsamples, nx, ny, nz = x_1.shape
    data = x_1.reshape((nsamples, nx * ny * nz))  # reshape data for UMAP

    # allow for choice of UMAP params and monitor embedding
    embedding_UMAP = umap.UMAP(**params).fit_transform(data)
    x = embedding_UMAP[:, 0]
    y = embedding_UMAP[:, 1]

    return x, y


# gets points from generated scatter plot
def get_points(x, y):
    figure, ax = plt.subplots()
    figure = ax.scatter(x, y)
    UMAP_points = figure.get_offsets().data
    return UMAP_points


# creates image coordinates from scatter plot points
def find_coordinates(points):
    x_coords = []
    y_coords = []

    for coordinates in points:
        x_coord = coordinates[0]
        y_coord = coordinates[1]
        x_coords.append(x_coord)
        y_coords.append(y_coord)

    # get min and max coordinates for x and y axes of all images
    y_coord_min = min(y_coords)
    x_coord_min = min(x_coords)
    y_coord_max = max(y_coords)
    x_coord_max = max(x_coords)
    return x_coord_max, x_coord_min, y_coord_max, y_coord_min, x_coords, y_coords


# finds min and max distances between points
def dist(p0, p1):
    return (((p0[0] - p1[0]) ** 2) + ((p0[1] - p1[1]) ** 2)) ** .5

# find distance between each image on the canvas and get appropriate scale factor for napari canvas
def scale_distance(points, img_width):
    distances = []
    for i in range(len(points) - 1):
        for j in range(i + 1, len(points)):
            distances += [dist(points[i], points[j])]  # distance of each image from each other

    # finds scale factor for image distance based on distance standard deviation and image size
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


# rescales points based on new scaled distance between points based on scale_factor
def rescale_points(x_coord_max, x_coord_min, y_coord_max, y_coord_min, len_of_array, x_coords, y_coords, scale_factor):
    # rename variables for clarity
    old_max_x = x_coord_max
    old_min_x = x_coord_min
    old_min_y = y_coord_min
    old_max_y = y_coord_max

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
    for old_value_x in x_coords:
        new_value_x = int((((old_value_x - old_min_x) * new_range_x) / old_range_x) + new_min_x)
        scaled_values_x.append(new_value_x)
    for old_value_y in y_coords:
        new_value_y = int((((old_value_y - old_min_y) * new_range_y) / old_range_y) + new_min_y)
        scaled_values_y.append(new_value_y)

    # get new scaled image coordinates
    scaled_coords = np.stack((scaled_values_x, scaled_values_y), axis=1)

    return scaled_coords


# defines napari viewer size by new image coordinates and inputs images
def view_UMAP(scaled_coords, imgs):
    # get min and max values of scaled x and y coordinates
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
