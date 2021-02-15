# Encoding: UTF-8
# File: test_rasters.py
# Creation: Monday January 4th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
import unittest
from pathlib import Path
from PIL import Image
import rasterio
from pyproj.crs import CRS
from rasterio.transform import Affine
import numpy as np
import matplotlib.pyplot as plt

# Geolabel Maker
from geolabel_maker.rasters.raster import Raster, RasterCollection, ZOOM2RES
from geolabel_maker.rasters.utils import color_mask, merge_masks
from geolabel_maker import speedups

# For windows
speedups.disable()

# Global variables
ROOT = Path("checkpoints/rasters")
TILE1_PATH = ROOT / "tile_512-4864.tif"
TILE2_PATH = ROOT / "tile_512-5120.tif"
MASK_BUILDINGS_PATH = ROOT / "tile_512-4864-label-buildings.png"
MASK_VEGETATION_PATH = ROOT / "tile_512-4864-label-vegetation.png"
MASK_COLOR_BUILDINGS_PATH = ROOT / "tile_512-4864-label-buildings-color.png"
MASK_COLOR_VEGETATION_PATH = ROOT / "tile_512-4864-label-vegetation-color.png"
MASK_PATH = ROOT / "tile_512-4864-label.png"

ROOT_ = Path("checkpoints/vectors")
CATEGORY_PATHS = [ROOT_ / "buildings.json", ROOT_ / "vegetation.json"]


class RasterUtilsTests(unittest.TestCase):

    def test_01_color_mask(self):
        image = Image.open(MASK_BUILDINGS_PATH).convert("RGB")
        mask = color_mask(np.array(image), color=(211, 211, 211))
        mask_checkpoint = np.array(Image.open(MASK_COLOR_BUILDINGS_PATH).convert("RGB"))
        assert np.array_equal(mask, mask_checkpoint)

    def test_02_merge_masks(self):
        mask1 = Image.open(MASK_COLOR_BUILDINGS_PATH).convert("RGB")
        mask2 = Image.open(MASK_COLOR_VEGETATION_PATH).convert("RGB")
        masks = [np.array(mask1), np.array(mask2)]
        mask = merge_masks(masks)
        mask_checkpoint = np.array(Image.open(MASK_PATH).convert("RGB"))
        assert np.array_equal(mask, mask_checkpoint)


class RasterTests(unittest.TestCase):

    def test_01_open(self):
        raster = Raster.open(TILE1_PATH)
        assert isinstance(raster.data, rasterio.io.DatasetReader), "Incorrect input data"
        assert tuple(raster.bounds) == (1843040.96, 5173590.399999999, 1843061.44, 5173610.88), "Incorrect bounds"
        assert raster.crs.to_epsg() == 3946, "Incorrect EPSG"

    def test_02_rasterio(self):
        raster = Raster.open(TILE1_PATH)
        raster_data = raster.to_rasterio()
        assert isinstance(raster_data, rasterio.DatasetReader), "Could not convert to rasterio DatasetReader"
        array = raster_data.read()
        assert array.shape == (3, 256, 256), "Array shape mismatch"

    def test_03_from_array(self):
        array = np.zeros((3, 256, 256))
        crs = CRS.from_epsg(3946)
        transform = Affine(0.08, 0.0, 1843040.96, 0.0, -0.08, 5173610.88)
        raster = Raster.from_array(array, crs=crs, transform=transform)
        assert isinstance(raster, Raster), "Opening a Raster from an array failed"
        assert tuple(raster.bounds) == (1843040.96, 5173590.399999999, 1843061.44, 5173610.88), "Incorrect bounds"
        assert raster.crs.to_epsg() == 3946, "Incorrect EPSG"

    def test_05_save(self):
        raster = Raster.open(TILE1_PATH)
        tmp_file = Path(TILE1_PATH).parent / "test_05_save.tmp.tif"
        raster.save(tmp_file)
        raster = Raster.open(tmp_file)
        assert isinstance(raster, Raster), "Could not load the saved raster"
        Path(tmp_file).unlink()

    def test_06_rescale(self, factor=2):
        raster = Raster.open(TILE1_PATH)
        raster_rescaled = raster.rescale(factor)
        assert isinstance(raster_rescaled, Raster), "Rescaling a raster did not returned a Raster"
        assert tuple(raster_rescaled.bounds) == tuple(raster.bounds), "The bounds should be the same"
        assert raster_rescaled.crs.to_epsg() == raster.crs.to_epsg(), "The EPSG should be the same"
        height, width = raster.data.shape
        assert raster_rescaled.data.shape == (int(height * factor), int(width * factor)), "Incorrect output shape"

    def test_07_zoom(self, zoom=17):
        raster = Raster.open(TILE1_PATH)
        raster_zoom = raster.zoom(zoom)
        assert isinstance(raster_zoom, Raster), "Zooming a raster did not returned a Raster"
        assert tuple(raster_zoom.bounds) == tuple(raster.bounds), "The bounds should be the same"
        assert raster_zoom.crs.to_epsg() == raster.crs.to_epsg(), "The EPSG should be the same"
        height, width = raster.data.shape
        x_res, y_res = raster.data.res
        x_factor = x_res / ZOOM2RES[zoom]
        y_factor = y_res / ZOOM2RES[zoom]
        assert raster_zoom.data.shape == (int(height * y_factor), int(width * x_factor)), "Incorrect output shape"

    def test_08_to_crs(self, crs="EPSG:4326"):
        raster = Raster.open(TILE1_PATH)
        raster_proj = raster.to_crs(crs)
        assert isinstance(raster_proj, Raster), "The projection a raster did not returned a Raster"
        assert raster_proj.crs.to_epsg() == CRS(crs).to_epsg(), "The destination CRS does not match"

    def test_09_crop(self):
        raster = Raster.open(TILE1_PATH)
        bbox = (1843045.92, 5173595.36, 1843056.48, 5173605.92)
        raster_crop = raster.crop(bbox)
        assert isinstance(raster_crop, Raster), "The projection of a raster did not returned a Raster"
        assert tuple(raster_crop.bounds) == bbox, "The bounds do not match"

    def test_10_plot_bounds(self):
        raster = Raster.open(TILE1_PATH)
        axes = raster.plot_bounds()
        assert isinstance(axes, plt.Axes), "Plots should return axes"

    def test_11_plot(self):
        raster = Raster.open(TILE1_PATH)
        axes = raster.plot()
        assert isinstance(axes, plt.Axes), "Plots should return axes"


class RasterCollectionTests(unittest.TestCase):

    def test_01_init(self):
        raster1 = Raster.open(TILE1_PATH)
        raster2 = Raster.open(TILE2_PATH)
        rasters = RasterCollection(raster1, raster2)
        assert isinstance(rasters, RasterCollection), "Loading a RasterCollection failed"
        assert len(rasters) == 2, "Length is incorrect"
        # Empty collection
        rasters = RasterCollection()
        assert isinstance(rasters, RasterCollection), "Loading a RasterCollection failed"
        assert len(rasters) == 0, "Length is incorrect"
        # Special case if the input is None
        rasters = RasterCollection(None)
        assert isinstance(rasters, RasterCollection), "Loading a RasterCollection failed"
        assert len(rasters) == 0, "Length is incorrect"

    def test_02_open(self):
        rasters = RasterCollection.open(TILE1_PATH, TILE2_PATH)
        assert isinstance(rasters, RasterCollection), "Loading a RasterCollection failed"
        assert len(rasters) == 2, "Length is incorrect"

    def test_03_to_crs(self, crs="EPSG:4326"):
        rasters = RasterCollection.open(TILE1_PATH, TILE2_PATH)
        rasters_proj = rasters.to_crs(crs)
        assert isinstance(rasters, RasterCollection), "Did not returned a RasterCollection"
        assert rasters_proj[0].crs.to_epsg() == CRS(crs).to_epsg(), "Destination CRS did not match"
        assert rasters_proj[1].crs.to_epsg() == CRS(crs).to_epsg(), "Destination CRS did not match"
        assert rasters_proj.crs.to_epsg() == CRS(crs).to_epsg(), "Destination CRS did not match"

    def test_04_crop(self):
        rasters = RasterCollection.open(TILE1_PATH, TILE2_PATH)
        bbox = (1843041.61, 5173581.43, 1843071.04, 5173606.13)
        rasters_cropped = rasters.crop(bbox)
        assert isinstance(rasters_cropped, RasterCollection), "Crop did not returned a RasterCollection"

    def test_05_plot_bounds(self):
        rasters = RasterCollection.open(TILE1_PATH, TILE2_PATH)
        axes = rasters.plot_bounds()
        assert isinstance(axes, plt.Axes), "Plots should return axes"

    def test_06_plot(self):
        rasters = RasterCollection.open(TILE1_PATH, TILE2_PATH)
        axes = rasters.plot()
        assert isinstance(axes, plt.Axes), "Plots should return axes"


if __name__ == '__main__':
    unittest.main()
