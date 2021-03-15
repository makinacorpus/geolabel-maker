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
from geolabel_maker.annotations import Classification, ObjectDetection, Segmentation
from geolabel_maker.vectors import Category
from geolabel_maker import speedups

# For windows
speedups.disable()

# Global variables
ROOT = Path("checkpoints/annotations")
ROOT_CATEGORIES = Path("checkpoints/vectors")


class ClassificationTests(unittest.TestCase):

    def test_01_init(self):
        classif = Classification()
        assert len(classif.images) == 0, "Number of images is incorrect"
        assert len(classif.categories) == 0, "Number of categories is incorrect"
        assert len(classif.annotations) == 0, "Number of annotations is incorrect"
        assert classif.info is not None, "Info section is unknown"

    def test_02_open(self):
        classif = Classification.open(ROOT / "classification.txt")
        assert len(classif.images) == 9, "Number of images is incorrect"
        assert len(classif.categories) == 2, "Number of categories is incorrect"
        assert len(classif.annotations) == 9, "Number of annotations is incorrect"
        assert classif.info is not None, "Info section is unknown"

        classif = Classification.open(ROOT / "classification.csv")
        assert len(classif.images) == 9, "Number of images is incorrect"
        assert len(classif.categories) == 2, "Number of categories is incorrect"
        assert len(classif.annotations) == 9, "Number of annotations is incorrect"
        assert classif.info is not None, "Info section is unknown"

        classif = Classification.open(ROOT / "classification.json")
        assert len(classif.images) == 9, "Number of images is incorrect"
        assert len(classif.categories) == 2, "Number of categories is incorrect"
        assert len(classif.annotations) == 9, "Number of annotations is incorrect"
        assert classif.info is not None, "Info section is unknown"

    def test_03_save(self):
        classif = Classification.open(ROOT / "classification.txt")
        tmp_file = "test_03_save.tmp.txt"
        classif.save(ROOT / tmp_file)
        classif_tmp = classif.open(ROOT / tmp_file)
        assert classif_tmp.annotations == classif.annotations, "Corrupted annotations"
        Path(ROOT / tmp_file).unlink()

    def test_04_build(self):
        categories = [Category.open(ROOT_CATEGORIES / "buildings.json", color="lightgray"),
                      Category.open(ROOT_CATEGORIES / "vegetation.json", color="green")]
        classif = Classification.build(
            dir_images=ROOT / "images",
            dir_labels=ROOT / "labels",
            categories=categories
        )
        classif.save(ROOT / "classification_build.json")

        assert len(classif.images) == 9, "Number of images is incorrect"
        assert len(classif.categories) == 2, "Number of categories is incorrect"
        assert len(classif.annotations) == 9, "Number of annotations is incorrect"
        assert classif.info is not None, "Info section is unknown"
        # Check that the build is correct
        classif_checkpoint = classif.open(ROOT / "classification_build.json")
        assert classif.__dict__ == classif_checkpoint.__dict__, "The annotations are different"

    def test_05_make(self):
        categories = [Category.open(ROOT_CATEGORIES / "buildings.json", color="lightgray"),
                      Category.open(ROOT_CATEGORIES / "vegetation.json", color="green")]
        classif = Classification.make(
            dir_images=ROOT / "images",
            categories=categories,
            pattern="*.tif"
        )
        classif.save(ROOT / "classification_make.json")
        assert len(classif.images) == 9, "Number of images is incorrect"
        assert len(classif.categories) == 2, "Number of categories is incorrect"
        assert len(classif.annotations) == 9, "Number of annotations is incorrect"
        assert classif.info is not None, "Info section is unknown"
        # Check that the build is correct
        classif_checkpoint = classif.open(ROOT / "classification_make.json")
        assert classif.__dict__ == classif_checkpoint.__dict__, "The annotations are different"

    def test_06_plot(self):
        classif = Classification.open(ROOT / "classification.txt")
        classif.plot()


class ObjectDetectionTests(unittest.TestCase):

    def test_01_init(self):
        objects = ObjectDetection()
        assert len(objects.images) == 0, "Number of images is incorrect"
        assert len(objects.categories) == 0, "Number of categories is incorrect"
        assert len(objects.annotations) == 0, "Number of annotations is incorrect"
        assert objects.info is not None, "Info section is unknown"

    def test_02_open(self):
        objects = ObjectDetection.open(ROOT / "objects.json")
        assert len(objects.images) == 9, "Number of images is incorrect"
        assert len(objects.categories) == 2, "Number of categories is incorrect"
        assert len(objects.annotations) == 15, "Number of annotations is incorrect"
        assert objects.info is not None, "Info section is unknown"

    def test_03_save(self):
        objects = ObjectDetection.open(ROOT / "objects.json")
        tmp_file = "objects_test_03_save.tmp.json"
        objects.save(ROOT / tmp_file)
        objects_tmp = objects.open(ROOT / tmp_file)

        assert objects_tmp.__dict__ == objects.__dict__, "Corrupted annotations"
        Path(ROOT / tmp_file).unlink()

    def test_04_build(self):
        categories = [Category.open(ROOT_CATEGORIES / "buildings.json", color="lightgray"),
                      Category.open(ROOT_CATEGORIES / "vegetation.json", color="green")]
        objects = ObjectDetection.build(
            dir_images=ROOT / "images",
            dir_labels=ROOT / "labels",
            categories=categories
        )
        assert len(objects.images) == 9, "Number of images is incorrect"
        assert len(objects.categories) == 2, "Number of categories is incorrect"
        assert len(objects.annotations) == 15, "Number of annotations is incorrect"
        assert objects.info is not None, "Info section is unknown"
        # Check that the build is correct
        objects_checkpoint = Segmentation.open(ROOT / "objects_build.json")
        assert objects.__dict__ == objects_checkpoint.__dict__, "The annotations are different"

    def test_05_make(self):
        categories = [Category.open(ROOT_CATEGORIES / "buildings.json", color="lightgray"),
                      Category.open(ROOT_CATEGORIES / "vegetation.json", color="green")]
        objects = ObjectDetection.make(
            dir_images=ROOT / "images",
            categories=categories
        )
        assert len(objects.images) == 9, "Number of images is incorrect"
        assert len(objects.categories) == 2, "Number of categories is incorrect"
        assert len(objects.annotations) == 42, "Number of annotations is incorrect"
        assert objects.info is not None, "Info section is unknown"
        # Check that the build is correct
        objects_checkpoint = ObjectDetection.open(ROOT / "objects_make.json")
        assert objects.__dict__ == objects_checkpoint.__dict__, "The annotations are different"

    def test_06_plot(self):
        objects = ObjectDetection.open(ROOT / "objects.json")
        objects.plot()


class SegmentationTests(unittest.TestCase):

    def test_01_init(self):
        segmentation = Segmentation()
        assert len(segmentation.images) == 0, "Number of images is incorrect"
        assert len(segmentation.categories) == 0, "Number of categories is incorrect"
        assert len(segmentation.annotations) == 0, "Number of annotations is incorrect"
        assert segmentation.info is not None, "Info section is unknown"

    def test_02_open(self):
        segmentation = Segmentation.open(ROOT / "segmentation.json")
        assert len(segmentation.images) == 9, "Number of images is incorrect"
        assert len(segmentation.categories) == 2, "Number of categories is incorrect"
        assert len(segmentation.annotations) == 15, "Number of annotations is incorrect"
        assert segmentation.info is not None, "Info section is unknown"

    def test_03_save(self):
        segmentation = Segmentation.open(ROOT / "segmentation.json")
        tmp_file = "segmentation_test_03_save.tmp.json"
        segmentation.save(ROOT / tmp_file)
        segmentation_tmp = segmentation.open(ROOT / tmp_file)
        assert segmentation_tmp.__dict__ == segmentation.__dict__, "Corrupted annotations"
        Path(ROOT / tmp_file).unlink()

    def test_04_build(self):
        categories = [Category.open(ROOT_CATEGORIES / "buildings.json", color="lightgray"),
                      Category.open(ROOT_CATEGORIES / "vegetation.json", color="green")]
        segmentation = Segmentation.build(
            dir_images=ROOT / "images",
            dir_labels=ROOT / "labels",
            categories=categories
        )
        segmentation.save(ROOT / "segmentation_build.json")
        assert len(segmentation.images) == 9, "Number of images is incorrect"
        assert len(segmentation.categories) == 2, "Number of categories is incorrect"
        assert len(segmentation.annotations) == 15, "Number of annotations is incorrect"
        assert segmentation.info is not None, "Info section is unknown"
        # Check that the build is correct
        segmentation_checkpoint = Segmentation.open(ROOT / "segmentation_build.json")
        assert segmentation.categories == segmentation_checkpoint.categories, "The annotations are different"

    def test_05_make(self):
        categories = [Category.open(ROOT_CATEGORIES / "buildings.json", color="lightgray"),
                      Category.open(ROOT_CATEGORIES / "vegetation.json", color="green")]
        segmentation = Segmentation.make(
            dir_images=ROOT / "images",
            categories=categories,
            pattern="*.tif"
        )
        assert len(segmentation.images) == 9, "Number of images is incorrect"
        assert len(segmentation.categories) == 2, "Number of categories is incorrect"
        assert len(segmentation.annotations) == 42, "Number of annotations is incorrect"
        assert segmentation.info is not None, "Info section is unknown"
        # Check that the build is correct
        segmentation_checkpoint = Segmentation.open(ROOT / "segmentation_make.json")
        assert segmentation.categories == segmentation_checkpoint.categories, "The annotations are different"

    def test_06_plot(self):
        segmentation = Segmentation.open(ROOT / "segmentation.json")
        segmentation.plot()


if __name__ == '__main__':
    unittest.main()
