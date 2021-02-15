# Encoding: UTF-8
# File: test_annotations.py
# Creation: Monday January 4th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
import unittest
from pathlib import Path

# Geolabel Maker
from geolabel_maker.annotations import COCO
from geolabel_maker.vectors import Category
from geolabel_maker import speedups

# For windows
speedups.disable()

# Global variables
ROOT = Path("checkpoints/annotations")
ROOT_CATEGORIES = Path("checkpoints/vectors")


class COCOTests(unittest.TestCase):

    def test_01_init(self):
        coco = COCO()
        assert len(coco.images) == 0, "Number of images is incorrect"
        assert len(coco.categories) == 0, "Number of categories is incorrect"
        assert len(coco.annotations) == 0, "Number of annotations is incorrect"
        assert coco.info is not None, "Info section is unknown"

    def test_02_open(self):
        coco = COCO.open(ROOT / "coco.json")
        assert len(coco.images) == 9, "Number of images is incorrect"
        assert len(coco.categories) == 2, "Number of categories is incorrect"
        assert len(coco.annotations) == 16, "Number of annotations is incorrect"
        assert coco.info is not None, "Info section is unknown"

    def test_03_save(self):
        coco = COCO.open(ROOT / "coco.json")
        tmp_file = "test_03_save.tmp.json"
        coco.save(ROOT / tmp_file)
        coco_tmp = coco.open(ROOT / tmp_file)
        assert coco_tmp.__dict__ == coco.__dict__, "Corrupted annotations"
        Path(ROOT / tmp_file).unlink()

    def test_04_build(self):
        categories = [Category.open(ROOT_CATEGORIES / "buildings.json", color="lightgray"),
                      Category.open(ROOT_CATEGORIES / "vegetation.json", color="green")]
        coco = COCO.build(
            images=ROOT / "images",
            categories=categories,
            labels=ROOT / "labels",
            pattern="*.tif"
        )
        assert len(coco.images) == 9, "Number of images is incorrect"
        assert len(coco.categories) == 2, "Number of categories is incorrect"
        assert len(coco.annotations) == 16, "Number of annotations is incorrect"
        assert coco.info is not None, "Info section is unknown"
        # Check that the build is correct
        coco_checkpoint = COCO.open(ROOT / "coco.json")
        assert coco.categories == coco_checkpoint.categories, "The annotations are different"

    def test_05_show(self):
        coco = COCO.open(ROOT / "coco.json")
        coco.show()


if __name__ == '__main__':
    unittest.main()
