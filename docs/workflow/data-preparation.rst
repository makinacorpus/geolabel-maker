================
Data Preparation
================

Geolabel Maker provides tools to process and simplify your data.
As your labels' quality depends on your data, this step should not be neglected.

Coordinate Reference System
===========================

If your data is in different coordinate reference system (CRS),
it is recommended to convert all of them in a unique CRS.
This will avoid doing multiple projections back and forth.

.. note::
    Make sure `GDAL <https://gdal.org/>`__ and `pyproj <https://pyproj4.github.io/pyproj/stable/>`__ 
    are correctly installed, and their versions are compatible. 
    Most of the errors you may encountered are due to this two packages.


Geographic Extent
=================

In addition, you may want to crop or clip the data.
Even though this step is optional, you should crop your data
to your area of interest to avoid manipulating large vectors and rasters. 

.. note::
    The clip process is only available for categories.


Simplify
========

The last step is to simplify your geometries. For example, you may want to remove small objects,
or merge those who are near or overlapping others.

.. note::
    The simplify process is only available for categories.
