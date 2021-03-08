# Encoding: UTF-8
# File: test_dataset.py
# Creation: Monday January 4th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
import unittest
from pathlib import Path
from shutil import rmtree
import json
import rasterio
from pyproj.crs import CRS
import matplotlib.pyplot as plt

# Geolabel Maker
from geolabel_maker import Dataset, speedups

# For windows
speedups.disable()

# Global variables
ROOT = Path("checkpoints/dataset")
ROOT_DATASET = ROOT / "data"


class DatasetTests(unittest.TestCase):

    def open_default(self):
        config = {
            "dir_images": "images",
            "dir_categories": "categories",
            "dir_labels": "labels"
        }
        config_path = ROOT / "data" / "config.json"
        with open(config_path, "w") as f:
            json.dump(config, f)

        return Dataset.open(config_path)

    def test_01_init(self):
        dataset = Dataset()
        assert len(dataset.images) == 0, "The number of loaded images is invalid"
        assert len(dataset.categories) == 0, "The number of loaded categories is invalid"
        assert len(dataset.labels) == 0, "The number of loaded labels is invalid"

    def test_02_open(self):
        dataset = Dataset.open(ROOT / "extern_config.json")
        assert len(dataset.images) == 9, "The number of loaded images is invalid"
        assert len(dataset.categories) == 2, "The number of loaded categories is invalid"
        assert len(dataset.labels) == 0, "The number of loaded labels is invalid"

    def test_03_from_dir(self):
        dataset = Dataset.from_dir(dir_images=ROOT_DATASET / "images", dir_categories=ROOT_DATASET / "categories")
        assert len(dataset.images) == 9, "The number of loaded images is invalid"
        assert len(dataset.categories) == 2, "The number of loaded categories is invalid"
        assert len(dataset.labels) == 0, "The number of loaded labels is invalid"
        Path("dataset.json").unlink()

    def test_04_from_root(self):
        dataset = Dataset.from_root(ROOT_DATASET)
        assert len(dataset.images) == 9, "The number of loaded images is invalid"
        assert len(dataset.categories) == 2, "The number of loaded categories is invalid"
        assert len(dataset.labels) == 9, "The number of loaded labels is invalid"
        assert Path(ROOT_DATASET / "dataset.json").exists(), "No 'dataset.json' file created"
        Path(ROOT_DATASET / "dataset.json").unlink()

    def test_05_save(self):
        dataset = self.open_default()
        tmp_file = Path(ROOT_DATASET / "test_04_save-tmp.json")
        dataset.save(tmp_file)
        dataset = Dataset.open(tmp_file)
        assert len(dataset.images) == 9, "The number of loaded images is invalid"
        assert len(dataset.categories) == 2, "The number of loaded categories is invalid"
        assert len(dataset.labels) == 9, "The number of loaded labels is invalid"
        # Remove config
        Path(tmp_file).unlink()

    def test_06_generate_labels(self):
        dataset = self.open_default()
        out_dir = ROOT_DATASET / "labels_tmp"
        dataset.generate_labels(out_dir=out_dir)
        assert len(dataset.labels) == 9
        # Remove dir
        rmtree(out_dir)

    def test_07_generate_vrt(self):
        dataset = self.open_default()
        images_vrt, labels_vrt = dataset.generate_vrt()
        raster_vrt = rasterio.open(ROOT_DATASET / "images.vrt")
        assert isinstance(raster_vrt, rasterio.io.DatasetReader), "Corrupted images VRT."
        raster_vrt = rasterio.open(ROOT_DATASET / "labels.vrt")
        assert isinstance(raster_vrt, rasterio.io.DatasetReader), "Corrupted labels VRT."
        # Remove files
        Path(images_vrt).unlink()
        Path(labels_vrt).unlink()

    def test_08_generate_tiles(self, zoom="17-20"):
        dataset = self.open_default()
        out_dir = ROOT_DATASET / "tiles_tmp"
        dataset.generate_tiles(zoom=zoom, out_dir=out_dir)
        images_dir = Path(out_dir / "images")
        labels_dir = Path(out_dir / "labels")
        assert images_dir.exists(), "The image tiles are missing"
        assert labels_dir.exists(), "The label tiles are missing"
        assert len(list(images_dir.rglob("*.png"))) == 19, "The number of generated image tiles is incorrect"
        assert len(list(labels_dir.rglob("*.png"))) == 19, "The number of generated label tiles is incorrect"
        # Remove dir
        rmtree(out_dir)

    def test_09_generate_mosaics(self):
        dataset = self.open_default()
        out_dir = ROOT_DATASET / "mosaics_tmp"
        dataset.generate_mosaics(out_dir=out_dir)
        images_dir = Path(out_dir / "images")
        labels_dir = Path(out_dir / "labels")
        assert images_dir.exists(), "The image mosaics are missing"
        assert labels_dir.exists(), "The label mosaics are missing"
        assert len(list(images_dir.rglob("*.tif"))) == 9, "The number of generated image mosaics is incorrect"
        assert len(list(labels_dir.rglob("*.tif"))) == 9, "The number of generated label mosaics is incorrect"
        rmtree(out_dir)

    def test_10_to_crs(self, crs="EPSG:4326"):
        dataset = self.open_default()
        dataset_proj = dataset.to_crs(crs)
        assert isinstance(dataset_proj, Dataset), "The projection of a dataset did not returned a Dataset"
        assert dataset_proj.crs.to_epsg() == CRS(crs).to_epsg(), "The destination CRS does not match"

    def test_11_crop(self):
        dataset = self.open_default()
        bbox = (1843045.92, 5173595.36, 1843056.48, 5173605.92)
        dataset_crop = dataset.crop(bbox)
        assert isinstance(dataset_crop, Dataset), "The projection of a dataset did not returned a Dataset"

    def test_12_plot_bounds(self):
        dataset = self.open_default()
        axes = dataset.plot_bounds()
        assert isinstance(axes, plt.Axes), "Plots should return axes"

    def test_13_plot(self):
        dataset = self.open_default()
        axes = dataset.plot()
        assert isinstance(axes, plt.Axes), "Plots should return axes"


if __name__ == '__main__':
    unittest.main()
