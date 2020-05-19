from osgeo import gdal
import rasterio
import rasterio.merge
from shutil import copyfile


def make_vrt(images, output_file='out.vrt'):
    """
        Builds a virtual raster from a list of rasters.

        Parameters
        ----------
        images : str
            the images directory path
        output_file : str
            the name of the output virtual raster. Default value is 'out.vrt'.
        Returns
        -------
            the GDAL VRT object
    """
    return gdal.BuildVRT(output_file, images)


def merge_rasters(rasters, output_file='merged.tif'):
    """
        Merge raster files from a specific directory to a single geotiff.

        Parameters
        ----------
        rasters : str
            the images directory path
        output_file : str
            the name of the final raster. Default value is 'merged.tif'.

        Returns
        -------
            the name of the final raster
    """
    if len(rasters) > 0:
        img_path = rasters[0].parent
        output_path = img_path / output_file

        if len(rasters) > 1:
            # open raster files
            src_files_to_mosaic = []
            for raster in rasters:
                src = rasterio.open(raster)
                src_files_to_mosaic.append(src)

            # merge raster images
            mosaic, output_transform = rasterio.merge.merge(
                src_files_to_mosaic
            )

            # create metadata for the merged raster
            output_metadata = src.meta.copy()
            output_metadata.update({"driver": "GTiff",
                                    "height": mosaic.shape[1],
                                    "width": mosaic.shape[2],
                                    "transform": output_transform})

            # write the merged raster
            with rasterio.open(output_path, "w", **output_metadata) as dest:
                dest.write(mosaic)

        elif len(rasters) == 1:
            copyfile(rasters[0], output_path)

    else:
        output_path = None

    return output_path
