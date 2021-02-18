# Encoding: UTF-8
# File: test_vectors.py
# Creation: Monday January 4th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
import unittest
from pathlib import Path
import geopandas as gpd
from pyproj.crs import CRS
import matplotlib.pyplot as plt

# Geolabel Maker
from geolabel_maker.vectors import Category, CategoryCollection

# Global variables
ROOT = Path("checkpoints/vectors")
RASTER_PATH = ROOT / "tile_512-4864.tif"
BUILDINGS_PATH = ROOT / "buildings.json"
VEGETATION_PATH = ROOT / "buildings.json"


class CategoryTests(unittest.TestCase):

    def test_01_init(self):
        data = gpd.read_file(BUILDINGS_PATH)
        category = Category(data, name="buildings", color=(255, 255, 255))
        assert isinstance(category.data, gpd.GeoDataFrame), "Loading a GeoDataFrame failed"
        assert len(category.data) == 17, "The number of geometries is incorrect"
        assert category.name == "buildings", "Name mismatch"
        assert tuple(category.color) == (255, 255, 255), "Color mismatch"
        assert tuple(category.bounds) == tuple(category.data.total_bounds), "Bounds mismatch"
        assert category.crs.to_epsg() == 3946, "Incorrect CRS"

    def test_02_open(self):
        category = Category.open(BUILDINGS_PATH, name="buildings", color=(255, 255, 255))
        assert isinstance(category, Category), "Loading a Category failed"
        assert len(category.data) == 17, "The number of geometries is incorrect"
        assert category.name == "buildings", "Name mismatch"
        assert tuple(category.color) == (255, 255, 255)

    def test_03_default(self):
        category = Category.open(BUILDINGS_PATH)
        assert category.color, "Color should not be None"
        data = gpd.read_file(BUILDINGS_PATH)
        category = Category(data, "buildings")
        assert category.color, "Color should not be None"
        assert category.name == "buildings", "Name mismatch"

    def test_04_save(self):
        category = Category.open(BUILDINGS_PATH)
        tmp_file = Path(BUILDINGS_PATH).parent / "test_02_save.tmp.tif"
        category.save(tmp_file)
        category = Category.open(BUILDINGS_PATH)
        assert isinstance(category, Category), "Corrupted category"
        assert len(category.data) == 17, "The number of geometries is incorrect"
        Path(tmp_file).unlink()

    def test_05_to_crs(self, crs="EPSG:4326"):
        category = Category.open(BUILDINGS_PATH)
        category_proj = category.to_crs(crs)
        assert isinstance(category, Category), "The projection should return a Category"
        assert category_proj.crs.to_epsg() == CRS(crs).to_epsg(), "Destination CRS did not match"

    def test_06_crop(self):
        category = Category.open(BUILDINGS_PATH)
        bbox = (1843041.61, 5173581.43, 1843071.04, 5173606.13)
        category_cropped = category.crop(bbox)
        assert isinstance(category_cropped, Category), "Crop did not returned a Category"
        assert len(category_cropped.data) == 6, "The number of geometries is incorrect"

    def test_07_plot_bounds(self):
        category = Category.open(BUILDINGS_PATH)
        axes = category.plot_bounds()
        assert isinstance(axes, plt.Axes), "Plots should return axes"

    def test_08_plot(self):
        category = Category.open(BUILDINGS_PATH)
        axes = category.plot()
        assert isinstance(axes, plt.Axes), "Plots should return axes"


class CategoryCollectionTests(unittest.TestCase):

    def test_01_init(self):
        category1 = Category.open(BUILDINGS_PATH)
        category2 = Category.open(VEGETATION_PATH)
        categories = CategoryCollection(category1, category2)
        assert isinstance(categories, CategoryCollection), "Loading a CategoryCollection failed"
        assert len(categories) == 2, "Length is incorrect"
        # Empty collection
        categories = CategoryCollection()
        assert isinstance(categories, CategoryCollection), "Loading a CategoryCollection failed"
        assert len(categories) == 0, "Length is incorrect"
        # Special case if the input is None
        categories = CategoryCollection(None)
        assert isinstance(categories, CategoryCollection), "Loading a CategoryCollection failed"
        assert len(categories) == 0, "Length is incorrect"

    def test_02_open(self):
        categories = CategoryCollection.open(BUILDINGS_PATH, VEGETATION_PATH)
        assert isinstance(categories, CategoryCollection), "Loading a CategoryCollection failed"
        assert len(categories) == 2, "Length is incorrect"
        assert tuple(categories[0].color) != tuple(categories[1].color), "The categories must have different colors"

    def test_03_to_crs(self, crs="EPSG:4326"):
        categories = CategoryCollection.open(BUILDINGS_PATH, VEGETATION_PATH)
        categories_proj = categories.to_crs(crs)
        assert isinstance(categories, CategoryCollection), "Did not returned a CategoryCollection"
        assert categories_proj[0].crs.to_epsg() == CRS(crs).to_epsg(), "Destination CRS did not match"
        assert categories_proj[1].crs.to_epsg() == CRS(crs).to_epsg(), "Destination CRS did not match"
        assert categories_proj.crs.to_epsg() == CRS(crs).to_epsg(), "Destination CRS did not match"

    def test_04_crop(self):
        categories = CategoryCollection.open(BUILDINGS_PATH, VEGETATION_PATH)
        bbox = (1843041.61, 5173581.43, 1843071.04, 5173606.13)
        categories_cropped = categories.crop(bbox)
        assert isinstance(categories_cropped, CategoryCollection), "Crop did not returned a CategoryCollection"

    def test_05_plot_bounds(self):
        categories = CategoryCollection.open(BUILDINGS_PATH, VEGETATION_PATH)
        axes = categories.plot_bounds()
        assert isinstance(axes, plt.Axes), "Plots should return axes"

    def test_06_plot(self):
        categories = CategoryCollection.open(BUILDINGS_PATH, VEGETATION_PATH)
        axes = categories.plot()
        assert isinstance(axes, plt.Axes), "Plots should return axes"

if __name__ == '__main__':
    unittest.main()
