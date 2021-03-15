=======
Install
=======

.. image:: https://img.shields.io/static/v1?label=Python&message=3.6&color=blue
   :target: https://img.shields.io/static/v1?label=Python&message=3.6&color=blue
   :alt: Python

.. image:: https://img.shields.io/pypi/v/geolabel-maker
    :target: https://pypi.org/project/geolabel-maker/
    :alt: PyPi


You can install :class:`geolabel-maker` through `PyPi <https://pypi.org/project/geolabel-maker>`__.
Use ``pip`` in your terminal:

.. code-block::

   pip install geolabel-maker


Alternatively, you can clone the package from github, with `git <https://git-scm.com/>`__:

.. code-block::

    git clone https://github.com/makinacorpus/geolabel-maker
    cd geolabel-maker
    python setup.py install


Dependencies
============

+-------------------------------------------------------------------+-------------------------------------+--------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| **Name**                                                          | **Long Name**                       | **Built Requirements**                                                   | **Description**                                                                             |
+-------------------------------------------------------------------+-------------------------------------+--------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| `GDAL <https://gdal.org/>`__                                      | Geospatial Data Abstraction Library | None                                                                     | Geospatial Data Abstraction Library                                                         |
+-------------------------------------------------------------------+-------------------------------------+--------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| `gdal2tiles <https://gdal.org/programs/gdal2tiles.html>`__        | Gdal To Tiles                       | GDAL                                                                     | A python library for generating map tiles based on gdal2tiles.py script.                    |
+-------------------------------------------------------------------+-------------------------------------+--------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| `geopandas <https://geopandas.org/>`__                            | GeoPandas                           | shapely, pandas, fiona, pyproj                                           | Geographic pandas extensions.                                                               |
+-------------------------------------------------------------------+-------------------------------------+--------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| `numpy <https://numpy.org/>`__                                    | NumPy                               | Built-in with anaconda.                                                  | NumPy is the fundamental package for array computing with Python.                           |
+-------------------------------------------------------------------+-------------------------------------+--------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| `pandas <https://pandas.org/>`__                                  | Pandas                              | numpy, pytz, python-dateutil                                             | Powerful data structures for data analysis, time series, and statistics.                    |
+-------------------------------------------------------------------+-------------------------------------+--------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| `sentinelsat <https://sentinelsat.readthedocs.io/en/stable/>`__   | SentinelSat                         | requests, geomet, html2text, click, tqdm, geojson, six                   | Utility to search and download Copernicus Sentinel satellite images.                        |
+-------------------------------------------------------------------+-------------------------------------+--------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| `osmtogeojson <https://github.com/tyrasd/osmtogeojson>`__         | OSM to GeoJSON                      | None                                                                     | Convert OSM response to GeoJSON.                                                            |
+-------------------------------------------------------------------+-------------------------------------+--------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| `opencv-python <https://opencv.org/>`__                           | Open Computer Vision                | numpy                                                                    | Wrapper package for OpenCV python bindings.                                                 |
+-------------------------------------------------------------------+-------------------------------------+--------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| `pillow <https://pillow.readthedocs.io/en/stable/>`__             | Python Imaging Library              | None                                                                     | Python Imaging Library.                                                                     |
+-------------------------------------------------------------------+-------------------------------------+--------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| `rasterio <https://rasterio.readthedocs.io/en/latest/>`__         | Rasterio                            | snuggs, affine, cligj, numpy, click-plugins, gdal, certifi, attrs, click | Fast and direct raster I/O for use with Numpy and SciPy.                                    |
+-------------------------------------------------------------------+-------------------------------------+--------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| `requests <https://requests.readthedocs.io/en/master/>`__         | Requests                            | chardet, certifi, idna, urllib3                                          | Python HTTP for Humans.                                                                     |
+-------------------------------------------------------------------+-------------------------------------+--------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| `shapely <https://shapely.readthedocs.io/en/stable/index.html>`__ | Shapely                             | None                                                                     | Geometric objects, predicates, and operations.                                              |
+-------------------------------------------------------------------+-------------------------------------+--------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| `pyproj <https://pyproj4.github.io/pyproj/stable/>`__             | PyProj                              | certifi                                                                  | Python interface to PROJ (cartographic projections and coordinate transformations library). |
+-------------------------------------------------------------------+-------------------------------------+--------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+


GDAL
====

Follow the next steps to install 
`GDAL <https://github.com/OSGeo/gdal>`__ on your machine.

.. warning::
    As a particular case, GDAL is not included in the ``setup.py``.


Ubuntu
------

For `Ubuntu` distributions, the following operations are needed to install this program:


.. code-block::

    sudo apt-get install libgdal-dev
    sudo apt-get install python3-gdal


The GDAL version can be verified by:

.. code-block::

    gdal-config --version


After that, a simple ``pip install gdal`` (or ``conda install gdal``) may be sufficient, 
however considering our own experience it is not the case on Ubuntu. 
One has to retrieve a GDAL for Python that corresponds to the GDAL of system:

.. code-block::

    pip install --global-option=build_ext --global-option="-I/usr/include/gdal" GDAL==`gdal-config --version`
    python3 -c "import osgeo;print(osgeo.__version__)"


Windows
-------

For Windows, the library can be manually downloaded from the 
`unofficial library releases <https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal>`__, 
which is the most efficient way to install it. 
You will need to download the version corresponding to your OS platform, then install it:

.. code-block::

    pip install <your_gdal_wheel>

