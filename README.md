# geolabel-maker

This tool is provided to help you in your **data preparation for geospatial artificial intelligence**.

![](medias/geolabel-maker.gif)

With `geolabel-maker`, you will be able to combine satellite or aerial imagery with
vector spatial data to create your own ground-truth dataset. This Python package can
generate your final dataset in the [COCO format](http://cocodataset.org/#home) for deep-learning models.


It is designed to link up these 4 needed steps :
 1. create labels from geometries and raster files;
 2. make virtual raster files to combine images and labels;
 3. split image and label virtual files creating tiles;
 4. create an annotation JSON file in the COCO format for a specific zoom level.

## Installation

### Requirements

 * Python 3.6
 * GDAL

### GDAL

As a particular case, GDAL is not included into the `setup.py` file.

For `Ubuntu` distributions, the following operations are needed to install this program:

```
sudo apt-get install libgdal-dev
sudo apt-get install python3-gdal
```

The GDAL version can be verified by:
```
gdal-config --version
```
After that, a simple `pip install gdal` (or `conda install gdal`) may be sufficient, however considering our own experience it is not the case on Ubuntu. One has to retrieve a GDAL for Python that corresponds to the GDAL of system:
```
pip install --global-option=build_ext --global-option="-I/usr/include/gdal" GDAL==`gdal-config --version`
python3 -c "import osgeo;print(osgeo.__version__)"
```
For other OS, please visit the `GDAL` installation documentation.


### Installation with pip
```
pip install geolabel-maker
```

## Usage

### Inputs

> An sample dataset is available in the `data/` folder. See the [Examples](#examples) paragraph to more information.

To create your labels and annotations in the COCO format, you need:

 * `IMG` : path to the folder containing the images to be labeled
 * `CATEGORIES` : a JSON file with an unique id for each, the description of expected categories
with path to vector label file, and color as RGB triplet.
 * `TILES` : a folder where the tiles (256x256 pixels images) will be recorded

Example of the categories file:

```json
{
    "category_1": {
        "id": 1,
        "file": "path to your category_1 vector file",
        "color": [150, 0, 0]
    },
    "category_2": {
        "id": 2,
        "file": "path to your category_2 vector file",
        "color": [255, 255, 255]
    }
}
```

##### Supported formats:

We use packages based on GDAL drivers.

 * for images, see [raster formats](https://gdal.org/drivers/raster/index.html) :
   * GeoTIFF,
   * JPEG2000,
   * ASCII Grid,
   * etc
 * for geometries, see [supported drivers](https://github.com/Toblerity/Fiona/blob/master/fiona/drvsupport.py) of the `fiona` package :
   * ESRI Shapefile,
   * GeoJSON,
   * GPKG,
   * etc

### Using the command-line interface

A command-line interface is proposed with 5 available
actions (`make_labels`, `make_rasters`, `make_tiles`, `make_annotations`
 and `make_all`).

#### Step-by-step commands

 **1. Create labels from geometries and raster files**

```
geolabels make_labels IMG CATEGORIES
```

 **2. Make virtual raster files to combine images and labels**

```
geolabels make_rasters IMG
```

 **3. Split image and label virtual files creating tiles**

```
geolabels make_tiles IMG_VRT LABEL_VRT TILES
```

 **4. Create an annotation JSON file in the COCO format for a specific zoom level**

```
geolabels make_annotations TILES CATEGORIES
```

Option:
- *--zoom*, the zoom level

#### Global command

To run the full process to get a ground truth in the COCO format, use the command:

```
geolabels make_all IMG TILES CATEGORIES
```

Option:
- *--zoom*, the zoom level

### Importing the package in Python code

```python
from geolabel_maker import geolabels

# Create labels from geometries and raster files
geolabels.make_labels(img, categories)
# Make virtual raster files to combine images and labels
images_vrt, labels_vrt = geolabels.make_rasters(img)
# Split image and label virtual files creating tiles
geolabels.make_tiles(images_vrt, labels_vrt, tiles)
# Create an annotation JSON file in the COCO format
geolabels.make_annotations(tiles, categories)

# OR
# Run the full process
geolabels.make_all(img, tiles, categories)
```

## Examples

The **`data/`** folder contains geometries (`vectors/`) from Lyon, published as open data in the website [https://data.grandlyon.com](https://data.grandlyon.com).
It contains also an example of a JSON file describing categories used to create labels.

This folder doesn't contain images because this type of file is too big to be supported in Github. 
To follow our example, just download these two files and put them in the folder `data/rasters/`:
- [1843_5173_08_CC46.tif](https://download.data.grandlyon.com/files/grandlyon/imagerie/ortho2018/ortho/GeoTiff_YcBcR/1km_8cm_CC46/1843_5173_08_CC46.tif)
- [1844_5173_08_CC46.tif](https://download.data.grandlyon.com/files/grandlyon/imagerie/ortho2018/ortho/GeoTiff_YcBcR/1km_8cm_CC46/1844_5173_08_CC46.tif)

### Notebooks

Some Jupyter notebooks (in French) are available :
- [Use_geolabel_maker.ipynb](notebooks/Use_geolabel_maker.ipynb) explains the process to build your ground truth.
- [Check_coco_annotations.ipynb](notebooks/Check_coco_annotations.ipynb) allows to explore your final annotations file.

## For developers

#### Install from source

```
git clone URL
cd geolabel-maker
pip install -e .
```

#### Pre-commit and linting

* [Install pre-commit](https://pre-commit.com/#install) and run `pre-commit install`
to check linting before committing.

* When you want, you can force a pre-commit on all the files :

```
pre-commit run --all-files
```

## Acknowledgements

We gratefully acknowledge the contributions of the people who 
helped get this project off of the ground, including people who 
beta tested the software, gave feedback, improved dependencies of 
code in service of this release, or otherwise supported the project.

Particularly thank you [Lucie Camanez](https://github.com/TrueCactus) 
to have initiate this project in its internship.

We also acknowledge [Adam Kelly](https://www.immersivelimit.com/) 
whose work has helped us in the development of this tool.


