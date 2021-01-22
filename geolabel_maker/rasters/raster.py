# Encoding: UTF-8
# File: raster.py
# Creation: Tuesday December 29th 2020
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2020, Makina Corpus


r"""
This module handles georeferenced raster image (usually ``.tif`` image).

.. code-block:: python

    from geolabel_maker.rasters import Raster
    
    raster = Raster.open("tile.tif")

"""


# Basic imports
from itertools import product
from pathlib import Path
import rasterio
import gdal2tiles


def to_raster(element, *args, **kwargs):
    r"""Convert an object to a ``Raster``.

    Args:
        element (any): Element to convert. 
            It can be a ``str``, ``Path``, ``rasterio.DatasetReader`` etc...

    Returns:
        Raster

    Examples:
        >>> raster = to_raster("tile.tif")
        >>> raster = to_raster(Path("tile.tif"))
        >>> raster = to_raster(rasterio.open("tile.tif"))
    """
    if isinstance(element, str):
        return Raster.open(element, *args, **kwargs)
    elif isinstance(element, Path):
        return Raster.open(str(element), *args, **kwargs)
    elif isinstance(element, rasterio.io.DatasetReader):
        return Raster(element, *args, **kwargs)
    elif isinstance(element, Raster):
        return element
    raise ValueError(f"Unknown element: Cannot convert {type(element)} to `Raster`.")


class Raster:
    """Defines a georeferenced image. This class encapsulates ``rasterio`` dataset,
    and defines custom auto-download and processing methods, to work with `geolabel_maker`.

    * :attr:`data` (rasterio.io.DatasetReader): The ``rasterio`` data corresponding to a georeferenced image.

    """

    __slots__ = ["data"]

    def __init__(self, data):
        if not isinstance(data, rasterio.io.DatasetReader):
            raise TypeError(f"Unknown type for the raster data.",
                            f"Got {type(data)} but expected `rasterio.io.DatasetReader`.",
                            f"Try opening the raster data with `Raster.open('path/to/raster.tif')` class method.")
        super().__init__()
        self.data = data

    @classmethod
    def open(cls, filename):
        data = rasterio.open(filename)
        return Raster(data)

    @classmethod
    def download(cls, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def from_postgis(cls, *args, **kwargs):
        raise NotImplementedError

    def numpy(self):
        return self.data.read()

    def generate_tiles(self, outdir="tiles", **kwargs):
        r"""Create tiles from a raster file (using GDAL)

        .. note::
            If the output directory ``outdir`` does not exist,
            it will be created.

        Args:
            outdir (str, optional): Path to the directory where the tiles will be saved.

        Examples:
            >>> raster = Raster.open("raster.tif")
            >>> raster.generate_tiles(outdir="tiles")
        """
        Path(outdir).mkdir(parents=True, exist_ok=True)
        # Generate tiles with `gdal2tiles`
        file_raster = self.data.name
        gdal2tiles.generate_tiles(file_raster, outdir, **kwargs)

    def generate_mosaic(self, width=256, height=256, outdir="mosaic"):
        """Generate a mosaic from the raster. 
        A mosaic is a division of the main raster into 'windows'.
        This method does not create slippy tiles.

        .. note::
            If the output directory ``outdir`` does not exist,
            it will be created.

        Args:
            width (int, optional): The width of the window. Defaults to ``256``.
            height (int, optional): The height of the window. Defaults to ``256``.
            outdir (str, optional): Path to the directory where the windows are saved. Defaults to ``"mosaic"``.

        Examples:
            >>> raster = Raster.open("raster.tif")
            >>> raster.generate_mosaic(width=256, height=256, outdir="mosaic")
        """
        Path(outdir).mkdir(parents=True, exist_ok=True)
        num_cols = self.data.meta['width']
        num_rows = self.data.meta['height']
        offsets = product(range(0, num_cols, width), range(0, num_rows, height))
        main_window = rasterio.windows.Window(col_off=0, row_off=0, width=num_cols, height=num_rows)
        for col_off, row_off in offsets:
            window = rasterio.windows.Window(col_off=col_off, row_off=row_off, width=width, height=height).intersection(main_window)
            transform = rasterio.windows.transform(window, self.data.transform)
            out_profile = self.data.profile.copy()
            out_profile['transform'] = transform
            out_profile['width'] = window.width
            out_profile['height'] = window.height
            out_path = Path(outdir) / f"tile_{window.col_off}-{window.row_off}.tif"
            with rasterio.open(out_path, 'w', **out_profile) as dst:
                dst.write(self.data.read(window=window))
        return outdir

    def __repr__(self):
        return f"Raster(name='{self.data.name}', bbox={tuple(self.data.bounds)}, crs={self.data.crs})"
