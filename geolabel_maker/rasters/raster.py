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

# Geolabel Maker
from .download import SentinelHubAPI


__all__ = [
    "to_raster",
    "Raster",
    "RasterCollection"
]


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
    if isinstance(element, (str, Path)):
        return Raster.open(str(element), *args, **kwargs)
    elif isinstance(element, rasterio.io.DatasetReader):
        return Raster(element, *args, **kwargs)
    elif isinstance(element, Raster):
        return element
    raise ValueError(f"Unknown element: Cannot convert {type(element)} to `Raster`.")


class Raster:
    r"""Defines a georeferenced image. This class encapsulates ``rasterio`` dataset,
    and defines custom auto-download and processing methods, to work with `geolabel_maker`.

    * :attr:`data` (rasterio.io.DatasetReader): The ``rasterio`` data corresponding to a georeferenced image.

    """

    def __init__(self, data, filename=None):
        if not isinstance(data, rasterio.io.DatasetReader):
            raise TypeError(f"Unknown type for the raster data.",
                            f"Got {type(data)} but expected `rasterio.io.DatasetReader`.",
                            f"Try opening the raster data with `Raster.open('path/to/raster.tif')` class method.")
        self.data = data
        self.filename = filename

    @classmethod
    def open(cls, filename):
        data = rasterio.open(filename)
        return Raster(data, filename=str(filename))

    @classmethod
    def download(cls, username, password, *args, **kwargs):
        """Download a collection of rasters from the `SentinelHub` API.

        Args:
            username (str): SentinelHub username.
            password (str): SentinelHub password.

        Returns:
            RasterCollection

        Examples:
            >>> username = "my_username"
            >>> password = "my_password"
            >>> rasters = Raster.download(username, password)
        """
        api = SentinelHubAPI(username, password)
        files = api.download(*args, **kwargs)
        return RasterCollection(files)

    @classmethod
    def from_postgis(cls, *args, **kwargs):
        """Load a raster image from a `PostgreSQL` database.

        """
        raise NotImplementedError

    def numpy(self):
        """Convert the raster image to a numpy array, of shape :math:`(C, X, Y)`

        Returns:
            numpy.ndarray
            
        Examples:
            >>> raster = Raster.open("tile.tif")
            >>> array = raster.to_numpy()
        """
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
            out_path = Path(outdir) / f"{Path(self.filename).stem}-tile_{window.col_off}x{window.row_off}.tif"
            with rasterio.open(out_path, 'w', **out_profile) as dst:
                dst.write(self.data.read(window=window))
        return outdir

    def __repr__(self):
        return f"Raster(name='{self.data.name}', bbox={tuple(self.data.bounds)}, crs={self.data.crs})"


class RasterCollection:
    r"""
    Defines a collection of ``Raster``.
    This class behaves similarly as a ``list``, excepts it is made only of ``Raster``.

    * :attr:`items` (list): List of rasters.

    """

    def __init__(self, *rasters):
        if not isinstance(rasters, (list, tuple, RasterCollection)):
            rasters = [rasters]
        elif isinstance(rasters, (list, tuple)) and len(rasters) == 1:
            rasters = rasters[0]
        if not rasters:
            rasters = []
        self.items = [to_raster(raster) for raster in rasters]

    def append(self, raster):
        r"""Add a ``Raster`` to the collection.

        Args:
            raster (Raster): The raster to add.

        Examples:
            >>> collection = RasterCollection()
            >>> raster = Raster.open("tile.tif")
            >>> collection.append(raster)
            >>> collection
                RasterCollection(
                  (0): Raster(filename='tile.tif')
                )
        """
        raster = to_raster(raster)
        self.items.append(raster)

    def extend(self, rasters):
        r"""Add multiple ``Raster`` to the collection.

        Args:
            rasters (list): List of raster to add.

        Examples:
            >>> collection = RasterCollection()
            >>> rasters = [Raster.open("tile1.tif"), Raster.open("tile2.tif")]
            >>> collection.extend(rasters)
            >>> collection
                RasterCollection(
                  (0): Raster(filename='tile1.tif')
                  (1): Raster(filename='tile2.tif')
                )
        """
        rasters = [to_raster(raster) for raster in rasters]
        self.items.extend(rasters)

    def __setitem__(self, index, raster):
        raster = to_raster(raster)
        self.items[index] = raster

    def __getitem__(self, index):
        return self.items[index]

    def __iter__(self):
        yield from self.items

    def __len__(self):
        return len(self.items)

    def __repr__(self):
        rep = f"RasterCollection("
        for i, raster in enumerate(self):
            rep += f"\n  ({i}): {raster}"
        rep += "\n)"
        return rep
