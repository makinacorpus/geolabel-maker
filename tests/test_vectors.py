# Encoding: UTF-8
# File: test_vectors.py
# Creation: Monday January 4th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
import unittest
import geopandas as gpd

# Geolabel Maker
from geolabel_maker.vectors import Category
from geolabel_maker.rasters import Raster


RASTER_PATH = "checkpoints/vectors/tile_512-4864.tif"
VECTOR_PATH = "checkpoints/vectors/buildings.json"


class CategoryTests(unittest.TestCase):

    def test_open(self):
        category = Category.open(VECTOR_PATH, name="buildings", color=(255, 255, 255))
        assert isinstance(category.data, gpd.GeoDataFrame)
        assert category.name == "buildings"
        assert category.color == (255, 255, 255)

    def test_crop(self):
        category = Category.open(VECTOR_PATH, name="buildings", color=(255, 255, 255))
        category_cropped = category.crop((1843000, 5173000, 1845000, 5174000))
        assert isinstance(category_cropped, Category)
        assert not category.data.empty

    def test_crop_raster(self):
        category = Category.open(VECTOR_PATH, name="buildings", color=(255, 255, 255))
        raster = Raster.open(RASTER_PATH)
        category_cropped = category.crop_raster(raster)
        assert isinstance(category_cropped, Category)
        assert not category.data.empty


if __name__ == '__main__':
    unittest.main()
