=======
Install
=======

.. image:: https://img.shields.io/static/v1?label=Python&message=3.6&color=blue
   :target: https://img.shields.io/static/v1?label=Python&message=3.6&color=blue
   :alt: Python


.. image:: https://img.shields.io/static/v1?label=GDAL&message=3.1.4&color=blue
   :target: https://img.shields.io/static/v1?label=GDAL&message=3.1.4&color=blue
   :alt: GDAL


.. |PyPi| image:: https://img.shields.io/pypi/v/geolabel-maker
    :target: https://pypi.org/project/geolabel-maker/


You can install ``geolabel-maker`` through `PyPi <https://pypi.org/project/geolabel-maker>`__.
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

In addition of the anaconda packages (``numpy``, ``matplotlib`` etc.), 
``geolabel-maker`` requires geo-science packages for image analysis:

* ``GDAL`` ,
* ``gdal2tiles`` ,
* ``geopandas`` ,
* ``shapely`` ,
* ``scikit-image`` ,
* ``proj4`` ,
* ``pyproj`` ,


GDAL
====

As a particular case, GDAL is not included in ``setup.py``.

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

For `Windows`, the library can be manually downloaded from the 
`unofficial library releases <https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal>`__, 
which is the most efficient way to install it. 
You will need to download the version corresponding to your OS platform, then install it:

.. code-block::

    pip install <your_gdal_wheel>


Other
-----

For other OS, please visit the `GDAL <https://github.com/OSGeo/gdal>`__ installation documentation.
