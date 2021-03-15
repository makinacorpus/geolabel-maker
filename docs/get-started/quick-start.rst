===========
Quick Start
===========

This section will guide you on how to use :class:`geolabel-maker` for the first time.
Make sure you installed it without any errors.

.. seealso::
   See `this section <install.html>`__ to install :class:`geolabel-maker`.


Set Up
======

The following example will illustrate how to generate and process labels and annotations from scratch.

First, download images and geometries from 
`Grand Lyon website <https://download.data.grandlyon.com>`__:

- **images:** download the following rasters in ``data/images``\ directory.
   
   - `1843_5173_08_CC46.tif <https://download.data.grandlyon.com/files/grandlyon/imagerie/ortho2018/ortho/GeoTiff_YcBcR/1km_8cm_CC46/1843_5173_08_CC46.tif>`__
   - `1844_5173_08_CC46.tif <https://download.data.grandlyon.com/files/grandlyon/imagerie/ortho2018/ortho/GeoTiff_YcBcR/1km_8cm_CC46/1844_5173_08_CC46.tif>`__

- **categories:** download the following geometries in the ``data/categories`` directory.
   
   - `buildings.json <https://download.data.grandlyon.com/wfs/grandlyon?SERVICE=WFS&VERSION=2.0.0&request=GetFeature&typename=cad_cadastre.cadbatiment&outputFormat=application/json;%20subtype=geojson&SRSNAME=EPSG:4171>`__
   - `vegetation.json <https://download.data.grandlyon.com/wfs/grandlyon?SERVICE=WFS&VERSION=2.0.0&request=GetFeature&typename=com_donnees_communales.comparcjardin_1_0_0&outputFormat=application/json;%20subtype=geojson&SRSNAME=EPSG:4171>`__
   - `bridges.json <https://download.data.grandlyon.com/wfs/grandlyon?SERVICE=WFS&VERSION=2.0.0&request=GetFeature&typename=fpc_fond_plan_communaut.fpcpont&outputFormat=application/json;%20subtype=geojson&SRSNAME=EPSG:4171>`__


Configuration
=============

Then, create the following configuration in ``data/dataset.json``\:

.. code-block::

   {
      "dir_images": "images",
      "dir_categories": "categories",
      "categories": [
         {
            "filename": "bridges.json",
            "name": "bridges",
            "color": "skyblue"
         },
         {
            "filename": "buildings.json",
            "name": "buildings",
            "color": "white"
         },
         {
            "filename": "vegetation.json",
            "name": "vegetation",
            "color": "green"
         }
      ]
   }

Your tree structure should be:

.. code-block::

   data
   ├── categories
   │   ├── bridges.json
   │   ├── buildings.json
   │   └── vegetation.json
   ├── images
   │   ├── 1843_5173_08_CC46.tif
   │   └── 1844_5173_08_CC46.tif   
   └── dataset.json


Workflow
========

Then, to create your annotations run the commands:

.. tabbed:: Python

   .. code-block:: python

      from geolabel_maker import Dataset
      from geolabel_maker.annotations import COCO

      # Open the dataset from your configuration
      dataset = Dataset.open("data/dataset.json")

      # Process
      dataset = dataset.to_crs("EPSG:3946", overwrite=True)
      dataset.categories = dataset.categories.clip(images.bounds, overwrite=True)

      # Create labels from geometries and raster files
      dataset.generate_labels()
      # Generate mosaics from images and labels
      dataset.generate_mosaics(zoom=18, width=500, height=500)

      # Create a COCO annotations
      annotation = COCO.build(
            dir_images="data/mosaics/images/18",
            dir_labels="data/mosaics/labels/18",
            colors={"bridges": "skyblue", "buildings": "white", "vegetation": "green"}
      )
      # Save the annotations
      annotation.save("coco.json")


.. tabbed:: Command Lines

   .. code-block::

      geolabel_maker labels --config data/dataset.json
      
      geolabel_maker mosaics --config data/dataset.json --zoom 18
      
      geolabel_maker annotations --dir_images data/mosaics/images --dir_labels data/mosaics/labels --colors bridges=skyblue,buildings=white,vegetation=green --type coco
