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
CLEAN_AFTER = True


class DatasetTests(unittest.TestCase):

    def test_01_init(self):
        dataset = Dataset()
        assert len(dataset.images) == 0, "The number of loaded images is invalid"
        assert len(dataset.categories) == 0, "The number of loaded categories is invalid"
        assert len(dataset.labels) == 0, "The number of loaded labels is invalid"

    def test_02_open(self):
        config = ROOT / "extern_config.json"
        dataset = Dataset.open(config)
        assert len(dataset.images) == 9, "The number of loaded images is invalid"
        assert len(dataset.categories) == 2, "The number of loaded categories is invalid"
        assert len(dataset.labels) == 0, "The number of loaded labels is invalid"

    def test_03_from_dir(self):
        root = ROOT / "data"
        dataset = Dataset.from_dir(dir_images=root / "images", dir_categories=root / "categories")
        assert len(dataset.images) == 9, "The number of loaded images is invalid"
        assert len(dataset.categories) == 2, "The number of loaded categories is invalid"
        assert len(dataset.labels) == 0, "The number of loaded labels is invalid"

    def test_04_from_root(self):
        root = ROOT / "data"
        dataset = Dataset.from_root(root)
        assert len(dataset.images) == 9, "The number of loaded images is invalid"
        assert len(dataset.categories) == 2, "The number of loaded categories is invalid"
        assert len(dataset.labels) == 0, "The number of loaded labels is invalid"
        assert Path(root / "dataset.json").exists(), "No 'dataset.json' file created"

    def test_05_save(self):
        root = ROOT / "data"
        dataset = Dataset.open(root / "intern_config.json")
        tmp_file = Path(root / "test_04_save-tmp.json")
        dataset.save(tmp_file)
        dataset = Dataset.open(tmp_file)
        assert len(dataset.images) == 9, "The number of loaded images is invalid"
        assert len(dataset.categories) == 2, "The number of loaded categories is invalid"
        assert len(dataset.labels) == 0, "The number of loaded labels is invalid"
        Path(tmp_file).unlink()

    def test_06_generate_labels(self):
        root = ROOT / "data"
        dataset = Dataset.open(root / "intern_config.json")
        dataset.generate_labels()
        assert len(dataset.labels) == 9

    def test_07_generate_vrt(self):
        root = ROOT / "data"
        dataset = Dataset.open(root / "intern_config.json")
        dataset.generate_vrt()
        images_vrt = rasterio.open(root / "images.vrt")
        assert isinstance(images_vrt, rasterio.io.DatasetReader)
        labels_vrt = rasterio.open(root / "labels.vrt")
        assert isinstance(labels_vrt, rasterio.io.DatasetReader)

    def test_08_generate_tiles(self):
        root = ROOT / "data"
        dataset = Dataset.open(root / "intern_config.json")
        dataset.generate_tiles(zoom="17-20")
        images_dir = Path(root / "tiles" / "images")
        labels_dir = Path(root / "tiles" / "labels")
        assert images_dir.exists(), "The image tiles are missing"
        assert labels_dir.exists(), "The label tiles are missing"
        assert len(list(images_dir.rglob("*.png"))) == 19, "The number of generated image tiles is incorrect"
        assert len(list(labels_dir.rglob("*.png"))) == 19, "The number of generated label tiles is incorrect"

    def test_09_generate_mosaics(self):
        root = ROOT / "data"
        dataset = Dataset.open(root / "intern_config.json")
        dataset.generate_mosaics()
        images_dir = Path(root / "mosaics" / "images")
        labels_dir = Path(root / "mosaics" / "labels")
        assert images_dir.exists(), "The image mosaics are missing"
        assert labels_dir.exists(), "The label mosaics are missing"
        assert len(list(images_dir.rglob("*.tif"))) == 9, "The number of generated image mosaics is incorrect"
        assert len(list(labels_dir.rglob("*.tif"))) == 9, "The number of generated label mosaics is incorrect"

    def test_10_to_crs(self, crs="EPSG:4326"):
        root = ROOT / "data"
        dataset = Dataset.open(root / "intern_config.json")
        dataset_proj = dataset.to_crs(crs)
        assert isinstance(dataset_proj, Dataset), "The projection of a dataset did not returned a Dataset"
        assert dataset_proj.crs.to_epsg() == CRS(crs).to_epsg(), "The destination CRS does not match"

    def test_11_crop(self):
        root = ROOT / "data"
        dataset = Dataset.open(root / "intern_config.json")
        bbox = (1843045.92, 5173595.36, 1843056.48, 5173605.92)
        dataset_crop = dataset.crop(bbox)
        assert isinstance(dataset_crop, Dataset), "The projection of a dataset did not returned a Dataset"

    def test_12_plot_bounds(self):
        root = ROOT / "data"
        dataset = Dataset.open(root / "intern_config.json")
        axes = dataset.plot_bounds()
        assert isinstance(axes, plt.Axes), "Plots should return axes"

    def test_13_plot(self):
        root = ROOT / "data"
        dataset = Dataset.open(root / "intern_config.json")
        axes = dataset.plot()
        assert isinstance(axes, plt.Axes), "Plots should return axes"

    def test_99_clean(self):
        if CLEAN_AFTER:
            clean()


def clean():
    root = ROOT / "data"
    config = Path(root / "dataset.json")
    images_vrt = Path(root / "images.vrt")
    labels_vrt = Path(root / "labels.vrt")
    dir_labels = root / "labels"
    dir_mosaics = root / "mosaics"
    dir_tiles = root / "tiles"

    try:
        config.unlink()
    except:
        print(f"ERROR: could not remove '{config}'.")

    try:
        images_vrt.unlink()
    except:
        print(f"ERROR: could not remove '{images_vrt}'.")

    try:
        labels_vrt.unlink()
    except:
        print(f"ERROR: could not remove '{labels_vrt}'.")

    try:
        rmtree(dir_labels)
    except:
        print(f"ERROR: could not remove '{dir_labels}'.")

    try:
        rmtree(dir_mosaics)
    except:
        print(f"ERROR: could not remove '{dir_mosaics}'.")

    try:
        rmtree(dir_tiles)
    except:
        print(f"ERROR: could not remove '{dir_tiles}'.")

    config = {
        "dir_images": "images",
        "dir_categories": "categories"
    }
    with open(root / "intern_config.json", "w") as f:
        json.dump(config, f, indent=4)


if __name__ == '__main__':
    unittest.main()
