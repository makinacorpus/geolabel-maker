"""Create label data from vector files"""

# Import
import numpy as np
import geopandas as gpd
import rasterio
import rasterio.mask
from shapely.geometry import box
from PIL import Image, ImageChops
import matplotlib.pyplot as plt
from pathlib import Path

from geolabel_maker import utils

Image.MAX_IMAGE_PIXELS = 156250000


def _select_vector(vector_file, raster_file,
                   save=False, output_file='subset.geojson'):
    """
    Get the geometries which are in the image's extent

    Parameters
    ----------
    vector_file : str
        vector file to extract
    raster_file : str
         raster file for reference
    save : bool
         saved the selection in a file or not
    output_file : str
        output file's name
        default value is "subset.geojson"

    Returns
    -------
    the geometries of the tif file's geographic extent
    """
    # read raster file
    raster_data = rasterio.open(raster_file)
    coordinate = raster_data.bounds
    # create a polygon from the raster bounds
    raster_bbox = box(*coordinate)

    # read vector file
    vector_data = gpd.read_file(vector_file)
    vector_data = vector_data.to_crs(raster_data.crs)
    # create a polygon from the raster bounds
    vector_bbox = box(*vector_data.total_bounds)

    if vector_bbox.contains(raster_bbox):
        # select vector data within the raster bounds
        Xmin, Xmax = coordinate.left, coordinate.right
        Ymin, Ymax = coordinate.bottom, coordinate.top
        subset = vector_data.cx[Xmin:Xmax, Ymin:Ymax]

        if save:
            # save the subset geodataframe in a file
            vector_path = Path(vector_file)
            subset_file = vector_path.parent / Path(output_file)
            subset.to_file(subset_file)
    else:
        raise ValueError('The geographic extents are not consistent.')

    return subset.geometry.values


def _create_label(raster_file, categories, dir_label=''):
    """
    Convert geometries to a raster file which could be used as label.

    Parameters
    ----------
    raster_file : str
        path of the raster file for reference
    categories : dict
        the dictionary containing for each category,
        a name and a color as (r, g, b) triplet
    dir_label : str
        path of the directory to save labels
        if it is empty, labels are registered with the origin raster file.
        default value is empty.

    Returns
    -------
    name of the created label image
    """
    with rasterio.open(raster_file) as src:
        # get metadata
        out_meta = src.meta

        img_list = []
        for name, infos in categories.items():
            out_image, out_transform = rasterio.mask.mask(
                src,
                infos['geometry'],
                crop=False
            )

            out_image = np.rollaxis(out_image, 0, 3)

            # convert image in black & color
            bw_image = utils.rgb2color(out_image, tuple(infos['color']))

            # create a PIL image
            img = Image.fromarray(bw_image.astype(rasterio.uint8))

            img_list.append(img)

    # merge images
    complete_img = img_list[0]
    if len(img_list) > 1:
        for img in img_list[1:]:
            complete_img = ImageChops.add(complete_img, img)

    # update metadata
    out_meta.update({"driver": "GTiff",
                     "height": complete_img.size[1],  # bw_image.shape[1],
                     "width": complete_img.size[0],  # bw_image.shape[2],
                     "count": 3,
                     "transform": out_transform})

    # create file path
    raster_path = Path(raster_file)
    output_file = "{}-label.tif".format(raster_path.stem)
    if dir_label:
        output_path = Path(dir_label) / output_file
    else:
        output_path = raster_path.parent / output_file

    # create a new raster containing labels
    with rasterio.open(output_path, "w", **out_meta) as dest:
        dest.write(np.rollaxis(np.array(complete_img), -1, 0))

    return output_path


def make_label(raster_file, categories, dir_label=''):
    """
    Make the label file corresponding to an image file.
    Labels are created with colors and geometries specified
    in the categories JSON file.

    Parameters
    ----------
    raster_file : str
         raster file for reference
    categories : str
         JSON file containing the description of categories
    dir_label : str
        path of the directory to save labels
        if it is empty, labels are registered with the origin raster file.
        default value is empty.

    Returns
    -------
    name of the created label image
    """
    for name, infos in categories.items():
        infos['geometry'] = _select_vector(infos['file'], raster_file)

    output_path = _create_label(raster_file, categories, dir_label)

    return output_path


def show(raster_file, label_file, img_size=512, title="",
         show=True, save=False):
    """
    Plot Image, Label and the superposition of the two.

    Parameters
    ----------
    raster_file : str
       raster_file name used for Image
    label_file: str
         Black and white tif file used for labelling
    img_size : int
        size of the displayed raster's part
        Default value is 512 pixels.
    title : str
        custom title to add to the plot
        Default value is empty.
    show : boolean
        if True, the figure is displayed.
        Default value is True.
    save : boolean
        if True, the figure is saved in a plots folder
        in the same directory as raster file. Default value is False.
    """
    # get raster file path
    raster_path = Path(raster_file)

    # read images
    im = Image.open(raster_file)
    lab = Image.open(label_file)

    # create figure
    figure, axis = plt.subplots(1, 3, figsize=(12, 6))
    axis[0].imshow(im)
    axis[1].imshow(lab, cmap="gray")
    axis[2].imshow(im)
    axis[2].imshow(lab, alpha=0.5)

    # select randomly a part of the rasters
    if img_size < np.min(im.size):
        randidx = np.random.randint(0, 1 + im.size[0] - img_size)
        randidy = np.random.randint(0, 1 + im.size[1] - img_size)

        axis[0].set_xlim([randidx, randidx + img_size])
        axis[1].set_xlim([randidx, randidx + img_size])
        axis[2].set_xlim([randidx, randidx + img_size])
        axis[0].set_ylim([randidy, randidy + img_size])
        axis[1].set_ylim([randidy, randidy + img_size])
        axis[2].set_ylim([randidy, randidy + img_size])

    # add title
    image_name = raster_path.stem
    figure.suptitle("{} Image, label from {}".format(title, image_name))

    if show:
        plt.show()

    if save:
        plots_directory = raster_path.parent / Path("plots")
        plots_directory.mkdir(parents=True, exist_ok=True)
        plot_file = 'plot-{}.png'.format(image_name)
        figure.savefig(str(plots_directory / Path(plot_file)))


if __name__ == '__main__':
    # example dataset
    raster_file = "../../../data/open-data/lyon/1844_5173_08_CC46.tif"
    categories_file = ""

    # make label from vector file corresponding to another raster file
    filename = make_label(raster_file, categories_file)
    # visualisation and save plot
    show(raster_file, filename, save=True)
