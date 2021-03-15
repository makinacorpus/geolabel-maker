============
Command Line
============

A command-line interface is proposed with the main actions. 
These commands work in a terminal containing a python environment.

:mod:`download`
===============

Downloads rasters or vectors 
from `Sentinel Hub <https://www.sentinel-hub.com/>`__, 
`MapBox <https://www.mapbox.com/>`__ or 
`OpenStreetMap <https://www.openstreetmap.org/>`__.

.. seealso::
    Follow the `configuration <../workflow/download.html#configuration>`__ template used to store credentials.

.. code-block:: text

    geolabel_maker  download  --config  Path to your configuration file, e.g. credentials.json


:mod:`labels`
=============

Creates `labels </workflow/dataset#labels>`__ / masks from satellite or aerial images and vector geometries.

.. seealso::
    Follow the `configuration <../workflow/dataset.html#configuration>`__ template to tune your dataset.

.. code-block:: text

    geolabel_maker  labels  --config          Path to your configuration file, e.g. dataset.json
                            --root            Path to the root dataset, e.g. ./             
                            --dir_images      Path to the images directory, e.g. images
                            --dir_categories  Path to the categories directory, e.g. categories
                            --images          List of images, e.g. images/tile1.tif images/tile2.tif 
                            --categories      list of categories, e.g. categories/buildings.json categories/vegetation.json


:mod:`mosaics`
==============

Generates `mosaics </workflow/dataset#mosaics>`__ of smaller size from the satellite images and labels.

.. seealso::
    Follow the `configuration <../workflow/dataset.html#configuration>`__ template to tune your dataset.

.. code-block:: text

    geolabel_maker  mosaics  --config          Path to your configuration file, e.g. dataset.json
                             --root            Path to the root dataset, e.g. ./             
                             --dir_images      Path to the images directory, e.g. images
                             --dir_categories  Path to the categories directory, e.g. categories
                             --dir_labels      Path to the labels directory, e.g. labels
                             --images          List of images, e.g. images/tile1.tif images/tile2.tif 
                             --categories      list of categories, e.g. categories/buildings.json categories/vegetation.json
                             --labels          List of labels, e.g. labels/tile1.tif labels/tile2.tif 
                             --zoom            Zoom level (i.e. resolution), e.g. 18

:mod:`tiles`
============

Generates `tiles </workflow/dataset#tiles>`__ of size 256x256 from the satellite images and labels.

.. seealso::
    Follow the `configuration <../workflow/dataset.html#configuration>`__ template to tune your dataset.

.. code-block:: text

    geolabel_maker labels  --config          Path to your configuration file, e.g. dataset.json
                           --root            Path to the root dataset, e.g. ./             
                           --dir_images      Path to the images directory, e.g. images
                           --dir_categories  Path to the categories directory, e.g. categories
                           --dir_labels      Path to the labels directory, e.g. labels
                           --images          List of images, e.g. images/tile1.tif images/tile2.tif 
                           --categories      list of categories, e.g. categories/buildings.json categories/vegetation.json
                           --labels          List of labels, e.g. labels/tile1.tif labels/tile2.tif 
                           --zoom            Zoom level (i.e. resolution), e.g. 18


:mod:`annotations`
==================

Generates an `annotations <../workflow/dataset.html#annotations>`__ file for the task of your choice.

.. code-block:: text

    geolabel_maker labels  --dir_images      Path to the images directory, e.g. images
                           --dir_categories  Path to the categories directory, e.g. categories                       
                           --dir_labels      Path to the labels directory, e.g. labels
                           --images          List of images, e.g. mosaics/images/18/tile1-tile_0x0.tif mosaics/images/18/tile2-tile_0x256.tif 
                           --categories      list of categories, e.g. categories/buildings.json categories/vegetation.json
                           --labels          List of labels, e.g. mosaics/labels/18/tile1-tile_0x0.tif mosaics/labels/18/tile2-tile_0x256.tif 
                           --colors          Names and colors associated to the labels / categories, e.g. buildings=white,vegetation=green
                           --type            Type of annotations to build, e.g. coco
                           --out_file        Name of the annotations file, e.g. coco.json
