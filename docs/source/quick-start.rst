===========
Quick Start
===========

This section will guide you on how to use ``geolabel-maker`` for the first time.
Make sure you installed it without any errors.

.. seealso::
   See `this section <install.html>`__ to install ``geolabel-maker``.


Set Up
======

To create your labels and annotations for segmentation, object-detection or classification, 
you will need a ``data/`` folder containing the following elements:

* ``images/`` : path to the folder containing the images to be labeled
* ``categories/`` : a JSON file with an unique id for each, the description of expected categories with path to vector label file, and color as RGB triplet.
* ``categories.json`` : a JSON file used to map the vectors (saved in ``categories/``) to their color and names.

Example of ``categories.json``:

.. code-block::

   {
      "category_1": {
         "id": 1,
         "file": "categories/category1.json",
         "color": [0, 150, 0]
      },
      ...,
      "category_9": {
         "id": 9,
         "file": "categories/category9.json",
         "color": [255, 255, 255]
      }
   }

The root folder ``data/`` should follow this template:

.. code-block::

   data
   ├── categories
   │   ├── category1.json
   │   ├── ...
   │   └── category9.json
   ├── images
   │   ├── satellite1.tif
   │   ├── ...
   │   └── satellite99.tif
   └── categories.json

.. note::
   The ``data/`` folder is used by ``geolabel-maker`` to store files in cache for the next operation.

.. warning::
   If you add images, categories while creating an annotations file, 
   you may break the process.
   Create a new ``data/`` root if you modified its content, 
   or clean the previous root folder from cached/generated files.


Workflow
========

You will need three commands / methods to generate your annotations.
THe steps are:


Create the labels
-----------------

Create the labels (raster images) from the categories (vectors).
The generated images will be saved under ``data/labels/`` folder.
These labels will be used as masks to extract polygons from the satellite images.

.. tabbed:: Python

   .. code-block:: python

      from geolabel_maker import Dataset

      # Open the dataset from the root
      dataset = Dataset.open(root="data")
      # Create labels from geometries and raster files
      dataset.generate_labels()

.. tabbed:: Command Lines

   .. code-block::

      geolabel_maker make_labels  --root  Path to the folder containing images and categories sub-folders


.. note::
   :badge:`optional,badge-info badge-pill`
   Merge the satellites images in a ``rasters.vrt`` file (same for the labels).
   If the virtual files ``.vrt`` do not exist, 
   they will be automatically created during the next step.

   .. tabbed:: Python

      .. code-block:: python

         dataset.generate_vrt()

   .. tabbed:: Command Lines

      .. code-block::

         geolabel_maker make_rasters --root  Path to the folder containing images and categories sub-folders


Generate tiles
--------------

Generate tiles from the satellite images and labels.

.. tabbed:: Python

   .. code-block:: python

      # Generate tiles from images and labels
      dataset.generate_tiles(zoom="14-20")

.. tabbed:: Command Lines

   .. code-block::

      geolabel_maker make_tiles --root  Path to the folder containing images and categories sub-folders
                                --zoom  (optional) Zoom interval e.g. 14-20

Generate annotations
--------------------

Generate your annotations file at the zoom of your choice.

.. tabbed:: Python

   .. code-block:: python

      from geolabel_maker.annotations import COCO

      # Create a COCO annotations
      annotation = COCO.from_dataset(dataset, zoom=17)
      # Save the annotations
      annotation.save("coco.json")

.. tabbed:: Command Lines

   .. code-block::

      geolabel_maker make_annotations --root  Path to the folder containing images and categories sub-folders
                                      --zoom  Zoom level used e.g. 17
                                      --type  Type of annotation e.g. coco
                                      --file  (optional) Output file e.g. coco.json


Example
=======

Set Up
------

Create a folder ``data/`` in your project folder.
Then, create the subfolders ``images/`` and ``categories/``.
Add the categories from `geolabel-maker repository <https://github.com/makinacorpus/geolabel-maker/tree/master/data/categories>`__.
Create the following ``categories.json`` and save it in the directory ``data/``:

.. code-block::

   {
      "vegetation": {
         "id": 1,
         "file": "categories/vegetation.json",
         "color": [0, 150, 0]
      },
      "buildings": {
         "id": 2,
         "file": "categories/buildings.json",
         "color": [255, 255, 255]
      }
   }


You can get satellite images published as open data in the website `https://data.grandlyon.com <https://data.grandlyon.com>`__.
Download these two files and put them in the folder ``data/images/``:

* `1843_5173_08_CC46.tif <https://download.data.grandlyon.com/files/grandlyon/imagerie/ortho2018/ortho/GeoTiff_YcBcR/1km_8cm_CC46/1843_5173_08_CC46.tif>`__
* `1844_5173_08_CC46.tif <https://download.data.grandlyon.com/files/grandlyon/imagerie/ortho2018/ortho/GeoTiff_YcBcR/1km_8cm_CC46/1844_5173_08_CC46.tif>`__

Your tree structure should be:

.. code-block::

   data
   ├── categories
   │   ├── buildings.json
   │   └── vegetation.json
   ├── images
   │   ├── 1843_5174_08_CC46.tif
   │   └── 1844_5173_08_CC46.tif   
   └── categories.json


Workflow
--------

Then, to create your annotations run the commands:

.. tabbed:: Python

   .. code-block:: python

      from geolabel_maker import Dataset
      from geolabel_maker.annotations import COCO

      # Open the dataset from the root
      dataset = Dataset.open("data")
      # Create labels from geometries and raster files
      dataset.generate_labels()
      # Generate tiles from images and labels
      dataset.generate_tiles(zoom="17-20")

      # Create a COCO annotations
      annotation = COCO.from_dataset(dataset, zoom=17)
      # Save the annotations
      annotation.save("coco.json")

.. tabbed:: Command Lines

   .. code-block::

      geolabel_maker make_labels --root data

      geolabel_maker make_tiles --root data --zoom 17-20

      geolabel_maker make_annotations --root data --zoom 17 --type coco --file coco.json
