"""Create COCO annotations"""

# Import
from pathlib import Path
import json
from datetime import datetime
from PIL import Image
import numpy as np
from skimage import measure
from shapely.geometry import Polygon


def _create_sub_masks(mask_image, colors):
    """
        Parameters
        ----------
        mask_image : PIL Image
        colors : list of triplets
            the list of colors used for the different categories
        Returns
        -------
        a dictionary of sub-masks indexed by RGB colors
    """
    width, height = mask_image.size

    # initialize a dictionary of sub-masks indexed by RGB colors
    sub_masks = {}
    for x in range(width):
        for y in range(height):
            # get the RGB values of the pixel
            pixel = mask_image.getpixel((x, y))

            # if the pixel has a color used in a category
            if pixel in colors:
                # check to see if we've created a sub-mask...
                sub_mask = sub_masks.get(pixel)
                if sub_mask is None:
                    # create a sub-mask (one bit per pixel)
                    # and add to the dictionary
                    # Note: we add 1 pixel of padding in each direction
                    # because the contours module doesn't handle cases
                    # where pixels bleed to the edge of the image
                    sub_masks[pixel] = Image.new('1', (width + 2, height + 2))

                # set the pixel value to 1 (default is 0),
                # accounting for padding
                sub_masks[pixel].putpixel((x + 1, y + 1), 1)

    return sub_masks


def _create_sub_mask_annotation(sub_mask, image_id, category_id,
                                annotation_id, is_crowd):
    """
            Parameters
            ----------
            sub_mask : PIL Image

            image_id : int

            category_id :int

            annotation_id : int

            is_crowd : bool

            Returns
            -------
             an annotation dictionary for the input sub-mask
    """
    # find contours (boundary lines) around each sub-mask
    # Note: there could be multiple contours if the object
    # is partially occluded. (E.g. an elephant behind a tree)
    contours = measure.find_contours(sub_mask, 0.5, positive_orientation='low')

    annotations = []
    for contour in contours:
        # flip from (row, col) representation to (x, y)
        # and subtract the padding pixel
        for i in range(len(contour)):
            row, col = contour[i]
            contour[i] = (col - 1, row - 1)

        # make a polygon and simplify it
        poly = Polygon(contour)
        poly = poly.simplify(1.0, preserve_topology=False)
        if not poly.is_empty:
            # create segmentation
            segmentation = np.array(poly.exterior.coords).ravel().tolist()

            # create annotation
            x, y, max_x, max_y = poly.bounds
            width = max_x - x
            height = max_y - y
            bbox = (x, y, width, height)
            area = poly.area

            annotation = {
                'segmentation': [segmentation],
                'iscrowd': int(is_crowd),
                'image_id': int(image_id),
                'category_id': int(category_id),
                'id': int(annotation_id),
                'bbox': bbox,
                'area': area
            }

            annotation_id += 1
            annotations.append(annotation)

    last_annotation_id = annotation_id
    return last_annotation_id, annotations


def _write_annotations(dir_label, images_ids, categories, is_crowd):
    """
        Parameters
        ----------
        dir_label : str
           path to the folder containing all label pictures
        images_ids : list of int
            the list of images id
        categories : dict
            the dictionary containing for each category,
            an unique id and a color as (r, g, b) triplet
        is_crowd : bool
            specifies whether the segmentation is for a single object (False)
            or for a group/cluster of objects (True)
        Returns
        -------
            the annotations' dictionary for all labels
    """
    # create an empty annotations' dictionary
    annotations_dict = {'annotations': []}

    dir_path = Path(dir_label)
    annotation_id = 1
    colors = [tuple(group['color']) for group in categories.values()]

    for file in dir_path.rglob("*.png"):
        print(file)
        # read label image
        mask = Image.open(file)
        mask = mask.convert("RGB")
        # create sub-masks
        sub = _create_sub_masks(mask, colors)
        # get image id
        filename = str(file.relative_to(dir_path))
        image_id = images_ids[filename]
        # create annotations
        annotations = []
        for color, sub_mask in sub.items():
            # find category id
            for infos in categories.values():
                if tuple(infos['color']) == color:
                    category_id = infos['id']
                    break
            # create a mask annotation
            last_annotation_id, annotations_new = _create_sub_mask_annotation(
                sub_mask,
                image_id,
                category_id,
                annotation_id,
                is_crowd
            )
            # save the created annotation and its id
            annotation_id = last_annotation_id + 1
            annotations += annotations_new

        # add these file's annotations in the final dictionary
        annotations_dict['annotations'] += annotations

    return annotations_dict


def _write_categories(categories_list):
    """
        Parameters
        ----------
        categories_list : list of str
           the list of category's names
        Returns
        -------
            the categories' dictionary
    """
    # create an empty categories' dictionary
    categories_dict = {'categories': []}

    for id, category in enumerate(categories_list):
        category_dict = {
            "id": id + 1,
            "name": category,
            "supercategory": category
        }
        categories_dict['categories'].append(category_dict)

    return categories_dict


def _write_images(dir_img):
    """
        Parameters
        ----------
        dir_img : str
           path to the folder containing all image tiles
        Returns
        -------
            the images' dictionary
    """
    # create an empty categories' dictionary
    images_dict = {'images': []}
    images_ids = {}

    dir_path = Path(dir_img)
    img_id = 1

    for file in dir_path.rglob("*.png"):
        # get image info
        img = Image.open(file)
        width, height = img.size
        filename = str(file.relative_to(dir_path))
        # create image description
        image = {
            "id": img_id,
            "width": width,
            "height": height,
            "file_name": filename}
        # add this description in the dictionary
        images_dict['images'].append(image)
        # save the id associated with each image
        images_ids[filename] = img_id
        # increment id for the next image
        img_id += 1

    return images_dict, images_ids


def _write_info(description, zoom):
    """
        Parameters
        ----------
        zoom : str
            zoom level used
        description : str
            dataset description
        Returns
        -------
            the info's dictionary
    """
    info_dict = {
        "info": {
            'description': description,
            'date_created': datetime.now().strftime('%Y/%m/%d'),
            'zoom': zoom

        }
    }

    return info_dict


def write_complete_annotations(dir_img, dir_label, categories, is_crowd, zoom,
                               description="Auto-generated by Geolabel-maker",
                               output_file="annotations.json"):
    """
        Parameters
        ----------
        dir_img : str
           path to the folder containing all image tiles
        dir_label : str
           path to the folder containing all label tiles
        categories : dict
            the dictionary containing for each category,
            an unique id and a color as (r, g, b) triplet
        is_crowd : bool
            specifies whether the segmentation is for a single object (False)
            or for a group/cluster of objects (True)
        zoom : str
            zoom level
        description : str
            dataset description.
            Default value is "Auto-generated by Geolabel-maker".
        output_file : str
            name of the annotation json file which will be created.
            Default name is "annotations.json".
        Returns
        -------
            the name of the annotation json file which will be created
    """
    # make info part
    info_dict = _write_info(description, zoom)

    # make images part
    images_dict, images_ids = _write_images(dir_img)

    # make annotations part
    annotations_dict = _write_annotations(
        dir_label,
        images_ids,
        categories,
        is_crowd
    )

    # make categories part
    categories_dict = _write_categories(list(categories.keys()))

    complete_annotations_dict = {
        **info_dict,
        **images_dict,
        **annotations_dict,
        **categories_dict,

    }

    # write json file
    with open(output_file, "w") as f:
        json.dump(complete_annotations_dict, f)

    return output_file
