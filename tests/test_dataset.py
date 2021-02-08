# Encoding: UTF-8
# File: test_dataset.py
# Creation: Monday January 4th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
import unittest
import rasterio
import shutil

from geolabel_maker import Dataset, speedups


# For windows
speedups.disable()


class DatasetTests(unittest.TestCase):

    def test_0_open(self):
        dataset = Dataset.open("data")
        assert len(dataset.images) == 9
        assert len(dataset.categories) == 2

    def test_1_generate_labels(self):
        dataset = Dataset.open("data")
        dir_labels = "data/labels"
        try:
            shutil.rmtree(dir_labels)
        except Exception as error:
            print(f"ERROR: Could not remove previous directory '{dir_labels}': {error}")
        dataset.generate_labels()
        assert len(dataset.labels) == 9

    def test_2_generate_vrt(self):
        dataset = Dataset.open("data")
        dir_labels = "data/labels"
        try:
            shutil.rmtree(dir_labels)
        except Exception as error:
            print(f"ERROR: Could not remove previous directory '{dir_labels}': {error}")
        dataset.generate_vrt()
        images_vrt = rasterio.open("data/images.vrt")
        assert isinstance(images_vrt, rasterio.io.DatasetReader)
        labels_vrt = rasterio.open("data/labels.vrt")
        assert isinstance(labels_vrt, rasterio.io.DatasetReader)

    def test_3_generate_tiles(self):
        dataset = Dataset.open("data")
        dir_tiles = "data/tiles"
        try:
            shutil.rmtree(dir_tiles)
        except Exception as error:
            print(f"ERROR: Could not remove previous directory '{dir_tiles}': {error}")
        dataset.generate_tiles(zoom="17-20")

    def test_4_generate_mosaics(self):
        dataset = Dataset.open("data")
        dir_mosaics = "data/mosaics"
        try:
            shutil.rmtree(dir_mosaics)
        except Exception as error:
            print(f"ERROR: Could not remove previous directory '{dir_mosaics}': {error}")
        dataset.generate_mosaics()

if __name__ == '__main__':
    unittest.main()
