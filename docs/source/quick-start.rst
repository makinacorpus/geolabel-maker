===========
Quick Start
===========

This section will guide you on how to use ``geolabel-maker`` for the first time.
Make sure you installed it without any errors.

.. seealso::
   See `this section <install.html>`__ to install ``geolabel-maker``.


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
      dataset = Dataset.open("data")

      # Create labels from geometries and raster files
      dataset.generate_labels()

.. tabbed:: Command Lines

   .. code-block::

      geolabel_maker make_labels  --config  (config or root required) Path to the configuration file used to create the dataset
                                  --root  (config or root required) Alternatively, the root of the dataset


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

         geolabel_maker make_labels --root  Path to the folder containing images and categories sub-folders


Generate tiles
--------------

Generate tiles from the satellite images and labels.

.. tabbed:: Python

   .. code-block:: python

      # Generate tiles from images and labels
      dataset.generate_tiles(zoom="14-20")

.. tabbed:: Command Lines

   .. code-block::

      geolabel_maker make_tiles --config  (config or root required) Path to the configuration file used to create the dataset
                                --root  (config or root required) Alternatively, the root of the dataset
                                --zoom  (optional) Zoom interval e.g. 14-20

Generate annotations
--------------------

Generate your annotations file at the zoom of your choice.

.. tabbed:: Python

   .. code-block:: python

      from geolabel_maker.annotations import COCO

      # Create a COCO annotations
      annotation = annotation = COCO.build(
         dir_images="mosaics/images/18",
         dir_labels="mosaics/labels/18",
         categories=dataset.categories
      )

      # Save the annotations
      annotation.save("coco.json")

.. tabbed:: Command Lines

   .. code-block::

      geolabel_maker make_annotations --config  (config or root required) Path to the configuration file used to create the dataset
                                      --root  (config or root required) Alternatively, the root of the dataset
                                      --dir_images  (optional) Directory containing satellite images
                                      --dir_labels  (optional) Directory containing label images
                                      --type  (optional) Type of annotation e.g. coco
                                      --file  (optional) Output file e.g. coco.json


Example
=======

Set Up
------

Create a folder ``data/`` in your project folder.
Then, create the subfolders ``images/`` and ``categories/``.
Add the categories from `geolabel-maker repository <https://github.com/makinacorpus/geolabel-maker/tree/master/data/categories>`__.
Create the following ``dataset.json`` and save it in the directory ``data/``:

.. code-block::

   {
      "dir_images": "images",
      "dir_categories": "categories",
      "dir_labels": "labels",
      "images": [
         {
               "id": 0,
               "filename": "1843_5173_08_CC46.tif"
         },
         {
               "id": 1,
               "filename": "1844_5173_08_CC46.tif"
         }
      ],
      "categories": [
         {
               "id": 0,
               "name": "buildings",
               "color": [
                  32,
                  160,
                  138
               ],
               "filename": "buildings.json"
         },
         {
               "id": 1,
               "name": "vegetation",
               "color": [
                  151,
                  243,
                  39
               ],
               "filename": "vegetation.json"
         }
      ]
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
   └── dataset.json


Workflow
--------

Then, to create your annotations run the commands:

.. tabbed:: Python

   .. code-block:: python

      from geolabel_maker import Dataset
      from geolabel_maker.annotations import COCO

      # Open the dataset from the root
      dataset = Dataset.open("data/dataset.json")

      # Create labels from geometries and raster files
      dataset.generate_labels()

      # Generate mosaics from images and labels
      dataset.generate_mosaics(zoom="18")

      # Create COCO annotations
      annotations = COCO.build(
         dir_images="data/mosaics/images/18",
         dir_labels="data/mosaics/labels/18",
         categories=dataset.categories
      )

      # Save the annotations
      annotations.save("coco.json")

.. tabbed:: Command Lines

   .. code-block::

      geolabel_maker make_labels --root data

      geolabel_maker make_mosaics --root data --zoom 18

      geolabel_maker make_annotations --root data --type coco --file coco.json
