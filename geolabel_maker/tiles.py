import gdal2tiles
from pathlib import Path, PurePath

from geolabel_maker import utils

IMG_TILES_DIR = 'images'
LABEL_TILES_DIR = "labels"
WEBVIEWER = 'openlayers'


def create_tiles(raster_file, dir_tiles):
    """
    Create tiles from a raster file (using GDAL)

    Parameters
    ----------
    raster_file : Pathstr
        the filename of a raster
    dir_tiles : Path
        the path to the directory where tiles will be saved
    """
    # Check if the tiles directory is empty, else clean it
    if not isinstance(dir_tiles, PurePath):
        dir_tiles = Path(dir_tiles)
    is_empty = not any(dir_tiles.iterdir())
    if not is_empty:
        utils.rm_tree(dir_tiles)

    options = {
        'webviewer': WEBVIEWER
    }

    gdal2tiles.generate_tiles(raster_file, dir_tiles, **options)


def get_tiles_directories(dir_tiles):
    """
    Get the name of tile folders (for images and for labels)

    Parameters
    ----------
    dir_tiles : str
            the path to the directory where tiles will be saved
    Returns
    -------
    the name of image and label tile folder
    """
    dir_imgtiles = Path(dir_tiles) / IMG_TILES_DIR
    dir_labeltiles = Path(dir_tiles) / LABEL_TILES_DIR

    return dir_imgtiles, dir_labeltiles
