import napari
from .main_window import MainWindow
from . import widget_definitions as wd

# set viewer as current viewer
viewer = wd.viewer

# run Main Window on napari
def main():
    viewer.window.add_dock_widget(MainWindow(), name='Image Similarity Search', area='right')
    napari.run()


if __name__ == '__main__':
    main()
