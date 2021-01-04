# Encoding: UTF-8
# File: test_dataset.py
# Creation: Monday January 4th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
import unittest
from shapely import speedups
import rasterio

from geolabel_maker import Dataset
from geolabel_maker.utils import rm_tree


# For windows
speedups.disable()


class DatasetTests(unittest.TestCase):

    def test_open(self):
        dataset = Dataset.open("data")
        assert len(dataset.images) == 9
        assert len(dataset.categories) == 2

    def test_generate_labels(self):
        dataset = Dataset.open("data")
        rm_tree(dataset.dir_labels)
        dataset.generate_labels()
        assert len(dataset.labels) == 9

    def test_generate_vrt(self):
        dataset = Dataset.open("data")
        rm_tree(dataset.dir_labels)
        dataset.generate_vrt()
        images_vrt = rasterio.open("data/images.vrt")
        assert isinstance(images_vrt, rasterio.io.DatasetReader)
        labels_vrt = rasterio.open("data/labels.vrt")
        assert isinstance(labels_vrt, rasterio.io.DatasetReader)

    def test_generate_tiles(self):
        dataset = Dataset.open("data")
        rm_tree(dataset.dir_tiles)
        dataset.generate_tiles(zoom="17-20")

    def test_extract_categories(self):
        dataset = Dataset.open("data")
        categories = dataset.extract_categories(zoom=20)
        assert len(categories) == 2
        names = [category.name for category in categories]
        assert "vegetation" in names
        assert "buildings" in names


if __name__ == '__main__':
    unittest.main()
