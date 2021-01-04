# Encoding: UTF-8
# File: test_rasters.py
# Creation: Monday January 4th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
import unittest
import rasterio
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

from geolabel_maker.rasters import Raster
from geolabel_maker.rasters.utils import rgb2color, rgb2gray, gray2bw


IMG_PATH = "checkpoints/rasters/tile_512-4864.tif"


class RasterTests(unittest.TestCase):

    def test_open(self):
        raster = Raster.open(IMG_PATH)
        assert isinstance(raster.data, rasterio.io.DatasetReader), "raster.data should be a rasterio.io.DatasetReader"

    def test_numpy(self):
        raster = Raster.open(IMG_PATH)
        array = raster.numpy()
        assert isinstance(array, np.ndarray), "raster.numpy() should return an array"
        assert array.shape == (3, 256, 256), "array shape mismatch"

    def test_rgb2gray(self):
        raster = Raster.open(IMG_PATH)
        array = raster.numpy()
        gray = rgb2gray(array)
        assert gray.shape == (256, 256), "Shape mismatch for gray image (X, Y)"
        array_path = Path(IMG_PATH).parent / f"{Path(IMG_PATH).stem}-gray.npy"
        # np.save(array_path, gray)
        gray_ref = np.load(array_path)
        assert np.array_equal(gray, gray_ref)
        image_path = Path(IMG_PATH).parent / f"{Path(IMG_PATH).stem}-gray-testoutput.png"
        plt.imsave(image_path, gray_ref, cmap="Greys_r")


if __name__ == '__main__':
    unittest.main()
