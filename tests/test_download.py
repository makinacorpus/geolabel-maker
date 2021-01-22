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

from geolabel_maker.rasters.download import SentinelHubAPI


class DownloadTests(unittest.TestCase):

    def test_0_download(self):
        bbox = (50, 7, 51, 8)
        api.download(bbox)


if __name__ == '__main__':
    unittest.main()
