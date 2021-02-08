Open this tutorial in a `Jupyter
Notebook <https://github.com/makinacorpus/geolabel-maker/blob/master/notebooks/Download%20Data.ipynb>`__

Download
========

You can download raster images and vector geometries on open access
platforms. This section will guide you on how to download satellite
images from `Sentinel Hub <https://www.sentinel-hub.com/>`__ and
geometries from `Open Street Map <https://www.openstreetmap.org/>`__.

Set Up
------

For this example, you will need to install some packages. -
``matplotlib`` for cool ploting. It should already be installed -
``pathlib`` for a modern implementation of system paths - ``shutil`` is
a package for file management - ``zipfile`` is a package to process
``.zip`` files - ``geopandas`` to create python ``DataFrame`` for
geo-information - ``rasterio`` is a package which uses GDAL to process
raster images - ``getpass`` for encrypted credentials - ``sentinelsat``
is the official API for ``SciHub``, the open access satellite platform
of the European Union - ``json`` for reading and writing ``json`` files
- ``requests`` to make requests to an URL endpoint - ``osmtogeojson`` is
used to convert Open Street Map responses to ``geojson`` format, useful
to work with ``geopandas``

.. code:: ipython3

    # Basic imports
    import matplotlib.pyplot as plt
    from pathlib import Path
    from shutil import copyfile
    import zipfile
    import geopandas as gpd
    
    # For SentinelHub
    from getpass import getpass
    import rasterio
    from sentinelsat import SentinelAPI
    
    # For OpenStreetMap
    import json
    import requests
    from osmtogeojson import osmtogeojson

If you are using windows, you may face some issues with ``shapely``.
Sometimes, turning down ``speedupds`` may improve the results. You can
ignore this cell if you are working on another platform.

.. code:: ipython3

    # For windows
    from shapely import speedups
    
    speedups.disable()

Satellite Images
----------------

In this section, we will download satellite images using the python API
``sentinelsat`` of `Sentinel Hub <https://www.sentinel-hub.com/>`__ . A
lot of utils are available, but only one will be explored in this
notebook. For more details, please visite the
`documentation <https://github.com/sentinelsat/sentinelsat>`__ of
``sentinelsat``.

Credentials
~~~~~~~~~~~

First of all, you will need to create an account on `Sentinel
Hub <https://services.sentinel-hub.com/oauth/subscription?origin=EOBrowser&param_client_id=1febe974-ca4f-44c1-9fc8-bafbd3bb4abd>`__.
You will need to provide an ``username`` and set a ``password``.

.. code:: ipython3

    username = getpass("SciHub Username: ")
    password = getpass("SciHub Password: ")


.. parsed-literal::

    SciHub Username:  ·········
    SciHub Password:  ···········
    

Bounding Box
~~~~~~~~~~~~

Sentinel Hub does not uses a bounding box, but works with WTK geodata.
Thus, you need to construct such data.

.. code:: ipython3

    bbox = (50, 7, 51, 8)
    
    lat_min, lon_min, lat_max, lon_max = bbox
    footprint = f"POLYGON(({lon_max} {lat_min},{lon_min} {lat_min},{lon_min} {lat_max},{lon_max} {lat_max},{lon_max} {lat_min}))"

Sentinel Hub API
~~~~~~~~~~~~~~~~

To make a request on the SciHub platform, use ``SentinelAPI`` class to
make your ``query``.

.. code:: ipython3

    from sentinelsat import SentinelAPI
    
    # Connect to the API
    api = SentinelAPI(username, password, "https://scihub.copernicus.eu/dhus")
    products = api.query(footprint,
                         date=("20200920", "20201020"),
                         platformname="Sentinel-2",
                         processinglevel = "Level-2A",
                         cloudcoverpercentage=(0, 10))

A good practice is to convert the response to a ``GeoDataFrame``, to
have a better overview of the available data.

.. code:: ipython3

    products_gdf = api.to_geodataframe(products)
    print(f"There are {len(products_gdf)} products found.")


.. parsed-literal::

    There are 6 products found.
    

.. parsed-literal::

    C:\Programs\anaconda3\lib\site-packages\pyproj\crs\crs.py:53: FutureWarning: '+init=<authority>:<code>' syntax is deprecated. '<authority>:<code>' is the preferred initialization method. When making the change, be mindful of axis order changes: https://pyproj4.github.io/pyproj/stable/gotchas.html#axis-order-changes-in-proj-6
      return _prepare_from_string(" ".join(pjargs))
    

.. code:: ipython3

    products_gdf.head()




.. raw:: html

    <div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }
    
        .dataframe tbody tr th {
            vertical-align: top;
        }
    
        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>title</th>
          <th>link</th>
          <th>link_alternative</th>
          <th>link_icon</th>
          <th>summary</th>
          <th>ondemand</th>
          <th>beginposition</th>
          <th>endposition</th>
          <th>ingestiondate</th>
          <th>orbitnumber</th>
          <th>...</th>
          <th>size</th>
          <th>s2datatakeid</th>
          <th>producttype</th>
          <th>platformidentifier</th>
          <th>orbitdirection</th>
          <th>platformserialidentifier</th>
          <th>processinglevel</th>
          <th>identifier</th>
          <th>uuid</th>
          <th>geometry</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>a6dea438-8bb6-48a2-9225-d30f04fea8b5</th>
          <td>S2A_MSIL2A_20200921T103031_N0214_R108_T32ULA_2...</td>
          <td>https://scihub.copernicus.eu/dhus/odata/v1/Pro...</td>
          <td>https://scihub.copernicus.eu/dhus/odata/v1/Pro...</td>
          <td>https://scihub.copernicus.eu/dhus/odata/v1/Pro...</td>
          <td>Date: 2020-09-21T10:30:31.024Z, Instrument: MS...</td>
          <td>false</td>
          <td>2020-09-21 10:30:31.024</td>
          <td>2020-09-21 10:30:31.024</td>
          <td>2020-09-21 20:07:10.835</td>
          <td>27418</td>
          <td>...</td>
          <td>1.02 GB</td>
          <td>GS2A_20200921T103031_027418_N02.14</td>
          <td>S2MSI2A</td>
          <td>2015-028A</td>
          <td>DESCENDING</td>
          <td>Sentinel-2A</td>
          <td>Level-2A</td>
          <td>S2A_MSIL2A_20200921T103031_N0214_R108_T32ULA_2...</td>
          <td>a6dea438-8bb6-48a2-9225-d30f04fea8b5</td>
          <td>MULTIPOLYGON (((6.23590 49.53173, 7.75278 49.5...</td>
        </tr>
        <tr>
          <th>b9436b02-733f-487a-b8dc-8b7d12e4a712</th>
          <td>S2A_MSIL2A_20200921T103031_N0214_R108_T32UMB_2...</td>
          <td>https://scihub.copernicus.eu/dhus/odata/v1/Pro...</td>
          <td>https://scihub.copernicus.eu/dhus/odata/v1/Pro...</td>
          <td>https://scihub.copernicus.eu/dhus/odata/v1/Pro...</td>
          <td>Date: 2020-09-21T10:30:31.024Z, Instrument: MS...</td>
          <td>false</td>
          <td>2020-09-21 10:30:31.024</td>
          <td>2020-09-21 10:30:31.024</td>
          <td>2020-09-21 20:05:11.074</td>
          <td>27418</td>
          <td>...</td>
          <td>1.12 GB</td>
          <td>GS2A_20200921T103031_027418_N02.14</td>
          <td>S2MSI2A</td>
          <td>2015-028A</td>
          <td>DESCENDING</td>
          <td>Sentinel-2A</td>
          <td>Level-2A</td>
          <td>S2A_MSIL2A_20200921T103031_N0214_R108_T32UMB_2...</td>
          <td>b9436b02-733f-487a-b8dc-8b7d12e4a712</td>
          <td>MULTIPOLYGON (((7.59072 50.45527, 9.13751 50.4...</td>
        </tr>
        <tr>
          <th>d2f0684c-252e-433d-aba5-5a7853cfa261</th>
          <td>S2A_MSIL2A_20200921T103031_N0214_R108_T31UGS_2...</td>
          <td>https://scihub.copernicus.eu/dhus/odata/v1/Pro...</td>
          <td>https://scihub.copernicus.eu/dhus/odata/v1/Pro...</td>
          <td>https://scihub.copernicus.eu/dhus/odata/v1/Pro...</td>
          <td>Date: 2020-09-21T10:30:31.024Z, Instrument: MS...</td>
          <td>false</td>
          <td>2020-09-21 10:30:31.024</td>
          <td>2020-09-21 10:30:31.024</td>
          <td>2020-09-21 20:03:50.223</td>
          <td>27418</td>
          <td>...</td>
          <td>553.17 MB</td>
          <td>GS2A_20200921T103031_027418_N02.14</td>
          <td>S2MSI2A</td>
          <td>2015-028A</td>
          <td>DESCENDING</td>
          <td>Sentinel-2A</td>
          <td>Level-2A</td>
          <td>S2A_MSIL2A_20200921T103031_N0214_R108_T31UGS_2...</td>
          <td>d2f0684c-252e-433d-aba5-5a7853cfa261</td>
          <td>MULTIPOLYGON (((7.35762 50.38212, 7.45059 51.3...</td>
        </tr>
        <tr>
          <th>47ddd2ab-ba37-47cd-bb94-a42d3dd3d959</th>
          <td>S2A_MSIL2A_20200921T103031_N0214_R108_T32ULB_2...</td>
          <td>https://scihub.copernicus.eu/dhus/odata/v1/Pro...</td>
          <td>https://scihub.copernicus.eu/dhus/odata/v1/Pro...</td>
          <td>https://scihub.copernicus.eu/dhus/odata/v1/Pro...</td>
          <td>Date: 2020-09-21T10:30:31.024Z, Instrument: MS...</td>
          <td>false</td>
          <td>2020-09-21 10:30:31.024</td>
          <td>2020-09-21 10:30:31.024</td>
          <td>2020-09-21 20:03:41.345</td>
          <td>27418</td>
          <td>...</td>
          <td>796.86 MB</td>
          <td>GS2A_20200921T103031_027418_N02.14</td>
          <td>S2MSI2A</td>
          <td>2015-028A</td>
          <td>DESCENDING</td>
          <td>Sentinel-2A</td>
          <td>Level-2A</td>
          <td>S2A_MSIL2A_20200921T103031_N0214_R108_T32ULB_2...</td>
          <td>47ddd2ab-ba37-47cd-bb94-a42d3dd3d959</td>
          <td>MULTIPOLYGON (((6.58271 50.43672, 7.72930 50.4...</td>
        </tr>
        <tr>
          <th>74df098c-0f1c-43ce-afe5-6db3d16660d5</th>
          <td>S2A_MSIL2A_20200921T103031_N0214_R108_T32UMA_2...</td>
          <td>https://scihub.copernicus.eu/dhus/odata/v1/Pro...</td>
          <td>https://scihub.copernicus.eu/dhus/odata/v1/Pro...</td>
          <td>https://scihub.copernicus.eu/dhus/odata/v1/Pro...</td>
          <td>Date: 2020-09-21T10:30:31.024Z, Instrument: MS...</td>
          <td>false</td>
          <td>2020-09-21 10:30:31.024</td>
          <td>2020-09-21 10:30:31.024</td>
          <td>2020-09-21 19:51:22.684</td>
          <td>27418</td>
          <td>...</td>
          <td>1.12 GB</td>
          <td>GS2A_20200921T103031_027418_N02.14</td>
          <td>S2MSI2A</td>
          <td>2015-028A</td>
          <td>DESCENDING</td>
          <td>Sentinel-2A</td>
          <td>Level-2A</td>
          <td>S2A_MSIL2A_20200921T103031_N0214_R108_T32UMA_2...</td>
          <td>74df098c-0f1c-43ce-afe5-6db3d16660d5</td>
          <td>MULTIPOLYGON (((7.61676 49.55649, 9.13497 49.5...</td>
        </tr>
      </tbody>
    </table>
    <p>5 rows × 36 columns</p>
    </div>



.. code:: ipython3

    products_gdf.plot()




.. parsed-literal::

    <AxesSubplot:>




.. image:: Download_Data_files%5CDownload_Data_13_1.png


Once you made your request, you can download the products with
``download()`` method. You can also specify the directory ``outdir``
where the images will be saved. Note that the downloaded images are
zipped.

.. code:: ipython3

    outdir_cache = "sentinel"
    # Create the output directory if it does not exist
    Path(outdir_cache).mkdir(parents=True, exist_ok=True)
    # Download all results from the search
    for product_id in products_gdf.index:
        # Download the products in the 'sentinel' directory
        api.download(product_id, outdir_cache)


.. parsed-literal::

    Downloading: 100%|████████████████████████████████████████████████████████████████| 1.10G/1.10G [09:19<00:00, 1.97MB/s]
    MD5 checksumming: 100%|████████████████████████████████████████████████████████████| 1.10G/1.10G [00:09<00:00, 119MB/s]
    Downloading: 100%|████████████████████████████████████████████████████████████████| 1.20G/1.20G [06:44<00:00, 2.96MB/s]
    MD5 checksumming: 100%|████████████████████████████████████████████████████████████| 1.20G/1.20G [00:09<00:00, 127MB/s]
    Downloading: 100%|███████████████████████████████████████████████████████████████████| 580M/580M [14:38<00:00, 661kB/s]
    MD5 checksumming: 100%|██████████████████████████████████████████████████████████████| 580M/580M [00:05<00:00, 103MB/s]
    Downloading: 100%|██████████████████████████████████████████████████████████████████| 836M/836M [11:26<00:00, 1.22MB/s]
    MD5 checksumming: 100%|██████████████████████████████████████████████████████████████| 836M/836M [00:06<00:00, 123MB/s]
    Downloading: 100%|████████████████████████████████████████████████████████████████| 1.21G/1.21G [19:31<00:00, 1.03MB/s]
    MD5 checksumming: 100%|████████████████████████████████████████████████████████████| 1.21G/1.21G [00:10<00:00, 111MB/s]
    Downloading: 100%|███████████████████████████████████████████████████████████████████| 801M/801M [16:10<00:00, 825kB/s]
    MD5 checksumming: 100%|██████████████████████████████████████████████████████████████| 801M/801M [00:07<00:00, 112MB/s]
    

The next step is to unzip all images. The following code will extract
all zipped files in the directory ``outdir``. It will also remove the
``.zip`` files.

.. code:: ipython3

    def extract_all(indir, outdir=None):
        outdir = outdir or indir
        # Extract all files in a directory
        for file in Path(indir).iterdir():
            filename = str(file)
            if zipfile.is_zipfile(filename):
                zipfile.ZipFile(filename, 'r').extractall(outdir)
            # Delete the zip file to keep only the unzip content
            file.unlink()
            
    
    # Extract all in the same folder, and remove the zipped files.
    extract_all(outdir_cache, outdir_cache)

You can now look the downloaded files. You will see that a lot of
metadata were also downloaded.

The images are in ``GRANULE/<PRODUCT>/IMG_DATA`` : You can retrieve the
metadata directly from the name of an image. For example,
``T31TCJ_20190225T105021_B02_10m.jp2``, the different parts of the name
seprated by ``_`` mean:

-  ``T31TCJ`` T + number of the tile
-  ``20190225T134315`` Date and time of the captured time, in the
   format: aaammjjThhmmss
-  ``B02`` Band (see the details of the bands below)
-  ``10m`` Resolution

Details of the images availble:

-  R10m:

   -  ``T31TCJ_20190225T105021_B02_10m.jp2``: blue
   -  ``T31TCJ_20190225T105021_B03_10m.jp2``: green
   -  ``T31TCJ_20190225T105021_B04_10m.jp2``: red
   -  ``T31TCJ_20190225T105021_TCI_10m.jp2``: true color image
   -  ``T31TCJ_20190225T105021_B08_10m.jp2``: NIR = near infrared
      (vegetation discrimination)
   -  ``T31TCJ_20190225T105021_WVP_10m.jp2``: water vapour
   -  ``T31TCJ_20190225T105021_AOT_10m.jp2``: top-of-atmosphere

-  R20m:

   -  ``T31TCJ_20190225T105021_B03_20m.jp2``: green
   -  ``T31TCJ_20190225T105021_B8A_20m.jp2``: NIR ~860nm (vegetation
      discrimination)
   -  ``T31TCJ_20190225T105021_SCL_20m.jp2``: scene classification
      map*\*
   -  ``T31TCJ_20190225T105021_TCI_20m.jp2``: true color image
   -  ``T31TCJ_20190225T105021_WVP_20m.jp2``: water vapour
   -  ``T31TCJ_20190225T105021_B12_20m.jp2``: SWIR ~2200nm
      (snow/ice/cloud discrimination)
   -  ``T31TCJ_20190225T105021_B04_20m.jp2``: red
   -  ``T31TCJ_20190225T105021_B02_20m.jp2``: blue
   -  ``T31TCJ_20190225T105021_B06_20m.jp2``: NIR ~750nm (vegetation
      discrimination)
   -  ``T31TCJ_20190225T105021_AOT_20m.jp2``: top-of-atmosphere
   -  ``T31TCJ_20190225T105021_B07_20m.jp2``: NIR ~775nm (vegetation
      discrimination)
   -  ``T31TCJ_20190225T105021_B05_20m.jp2``: NIR ~700nm (vegetation
      discrimination)
   -  ``T31TCJ_20190225T105021_B11_20m.jp2``: SWIR ~1600nm
      (snow/ice/cloud discrimination)

-  R60m:

   -  ``T31TCJ_20190225T105021_B03_60m.jp2``: green
   -  ``T31TCJ_20190225T105021_B04_60m.jp2``: red
   -  ``T31TCJ_20190225T105021_B11_60m.jp2``: SWIR ~1600nm
      (snow/ice/cloud discrimination)
   -  ``T31TCJ_20190225T105021_B05_60m.jp2``: NIR ~700nm (vegetation
      discrimination)
   -  ``T31TCJ_20190225T105021_B12_60m.jp2``: SWIR ~2200nm
      (snow/ice/cloud discrimination)
   -  ``T31TCJ_20190225T105021_WVP_60m.jp2``: water vapour
   -  ``T31TCJ_20190225T105021_B01_60m.jp2``: blue ~450nm (aerosols
      discrimination)
   -  ``T31TCJ_20190225T105021_SCL_60m.jp2``: scene classification map
   -  ``T31TCJ_20190225T105021_AOT_60m.jp2``: top-of-atmosphere
   -  ``T31TCJ_20190225T105021_B07_60m.jp2``: NIR ~775nm (vegetation
      discrimination)
   -  ``T31TCJ_20190225T105021_B06_60m.jp2``: NIR ~750nm (vegetation
      discrimination)
   -  ``T31TCJ_20190225T105021_B09_60m.jp2``: NIR ~840nm (water vapour
      discrimination)
   -  ``T31TCJ_20190225T105021_TCI_60m.jp2``: true color image
   -  ``T31TCJ_20190225T105021_B02_60m.jp2``: blue
   -  ``T31TCJ_20190225T105021_B8A_60m.jp2``: NIR ~860nm (vegetation
      discrimination)

\*\* scene classification map is a classification map which includes
four different classes for clouds (including cirrus) and six different
classifications for shadows, cloud shadows, vegetation, soils/deserts,
water and snow.

Process RGB images
~~~~~~~~~~~~~~~~~~

For ``geolabel-maker``, you may just need RGB images a.k.a. true color
image ``TCI``.

The following function will explore the downloaded products, find the
true color image at a specific ``resolution`` and move them to the
directory ``images``.

.. code:: ipython3

    def find_image(product_path, resolution=10, bandname="TCI"):
        product_dir = Path(product_path).parent
        product_name = Path(product_path).name
        granule_dir = product_dir / f"{product_name}.SAFE" / "GRANULE"
    
        for res_dir in granule_dir.iterdir():
            image_dir = res_dir / "IMG_DATA" / f"R{resolution}m"
            for image_file in image_dir.iterdir():
                if image_file.stem.endswith(f"{bandname.upper()}_{resolution}m"):
                    return image_file
    
    
    outdir = "images"
    resolution = 10
    bandname = "TCI"
    # Copy / move the true color images "TCI" in an other folder
    for product_name in products_gdf.title:
        product_path = Path(outdir_cache) / product_name
        image_file = find_image(product_path, resolution=resolution, bandname=bandname)
        # Move/copy the image to the main directory
        out_image = Path(outdir) / Path(image_file).name
        copyfile(str(image_file), str(out_image))

Use Geolabel Maker
~~~~~~~~~~~~~~~~~~

You have everything to work with ``geolabel-maker``. You can ``open``,
``merge`` the previously downloaded image and create a ``Dataset``.
Let’s merge all the downloaded rasters and visualize them.

.. code:: ipython3

    import sys
    sys.path.append("../")
    
    from geolabel_maker.rasters import Raster, generate_vrt

.. code:: ipython3

    rasters = []
    for image_file in Path("images").iterdir():
        rasters.append(Raster.open(image_file))
        
    generate_vrt("images.vrt", rasters)
    merged_raster = Raster.open("images.vrt")

Visualize the results
~~~~~~~~~~~~~~~~~~~~~

Finally, you can visualize the merged rasters with ``matplotlib``.

.. code:: ipython3

    fig, ax = plt.subplots(figsize=(5, 10))
    
    plt.imshow(merged_raster.numpy().transpose((1, 2, 0)))
    plt.axis("off")




.. parsed-literal::

    (-0.5, 10979.5, 20975.5, -0.5)




.. image:: Download_Data_files%5CDownload_Data_25_1.png


Vectors and Categories
======================

The next step is to retrieve geometries in a vector format. `Open Street
Map <https://www.openstreetmap.org>`__ is an open access platform for
geodata. You can download roads, buildings, vegetation area (and more)
in a vector (``json`` or ``osm`` format).

To retrieve data from their patform, there are two options: \* Use their
website \* Use their API

OSM data from the website
-------------------------

Go to `Open Street Map <https://www.openstreetmap.org>`__, then click on
``Export`` button. You will be redirected to a
`map <https://www.openstreetmap.org/export#map=10/48.8710/2.4142>`__,
centered near your position. Drag and drop the map to change the
location. You can select an area to download with the
``Manually select a different area`` button under the bbox, located in
the left panel. To download (all) the data, click on the blue ``Export``
button in the left panel. Thats it !

OSM data from the API
---------------------

Alternatively, you can connect to OSM API to retrieve lattest
geometries. You can directly connect to ``openstreetmap`` and make your
request, or use the ``overpass`` server used to retrieve larger area. In
this notebook, we will use the Overpass API.

Connect to the API
~~~~~~~~~~~~~~~~~~

To connect to the API, you use python packages (``overpass``) or make
your requests directly to the server.

.. code:: ipython3

    url = "http://overpass-api.de/api/interpreter"

Then, you will need to create a query. OSM uses a custom query system,
which is not easyto learn at first. The following query will retrieve
buildings within a bbox (south, west, north, east).

.. code:: ipython3

    query = """
    [out:json][timeout:700];
    (way["building"](47,8,48,9);
    relation["building"](47,8,48,9);
    );
    out body;
    >;
    out skel qt;
    """

Then, make get your request from OSM server with the package
``request``:

.. code:: ipython3

    response = requests.get(url, params={'data': query})
    json_data = response.json()

Custom queries
~~~~~~~~~~~~~~

You can adapt the above code for custom queries:

.. code:: ipython3

    bbox = (50, 7, 51, 8)
    lat_min, lon_min, lat_max, lon_max = bbox
    selector = '"building"'
    timeout = 700
    
    query = f"""
    [out:json][timeout:{timeout}];
    (relation[{selector}]({lat_min},{lon_min},{lat_max},{lon_max});
    way[{selector}]({lat_min},{lon_min},{lat_max},{lon_max});
    );
    out body;
    >;
    out skel qt;
    """

Make a request
~~~~~~~~~~~~~~

Again, use the ``requests`` package to make a request on OSM server. As
seen above, the response is in ``json`` format, but not ``geojson``.

.. code:: ipython3

    response = requests.get(url, params={'data': query})
    json_data = response.json()

Convert the request to geojson
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To convert the response to ``geojson``, we will use the ``osmtogeojson``
python package. It will convert a ``json`` response into a ``geojson``
format. > The package ``osm2geosjon`` is exactly the same, but slowly

.. code:: ipython3

    result = osmtogeojson.process_osm_json(json_data)

You can also use ``GDAL`` in commandlines to convert an OSM response to
``geojson``.

To check the content of the file, use:

::

   ogrinfo map.osm

Then:

::

   ogr2ogr -f GeoJSON map_multipolygons.geojson map.osm multipolygons

Save the result
^^^^^^^^^^^^^^^

Then, use the ``geopandas`` package to convert the results to a
dataframe, visualize them or save as a ``geojson``.

.. code:: ipython3

    df = gpd.GeoDataFrame.from_features(result)
    df.to_file("buildings.json", driver="GeoJSON")

Visualize the data
~~~~~~~~~~~~~~~~~~

You can use ``geopandas`` to visualize the data you downloaded.

.. code:: ipython3

    df.head()

.. code:: ipython3

    fig, ax = plt.subplots(figsize=(15, 15))
    df.plot(cmap='tab10', alpha=0.7, ax=ax)
