===========
Annotations
===========

The final step is to generate your annotations file. 
This step may be optional if your model only requires rasters as ground truth, 
like generative adversarial networks. 
However, some models require annotations in other formats like 
`Mask R-CNN <https://towardsdatascience.com/computer-vision-instance-segmentation-with-mask-r-cnn-7983502fcad1>`__ for instance segmentation, 
`YOLO <https://towardsdatascience.com/yolo-you-only-look-once-real-time-object-detection-explained-492dc9230006>`__ for object detection 
or `ResNet <https://towardsdatascience.com/an-overview-of-resnet-and-its-variants-5281e2f56035>`__ for classification tasks.

You can either generate the annotations using the previous labels or directly from the vector geometries.

.. image:: ../medias/figure-annotations.png
   :target: ../medias/figure-annotations.png
   :alt: annotations

Classification
==============

These annotations are used to know if a category is visible from an image.

.. note::
    This annotations file is a table and can be saved
    in ``CSV``\, ``TXT``\, ``JSON``\ formats.


Object Detection
================

These annotations are used to know the bounding box / localization of objects in images.

.. note::
    This annotations file is in ``JSON``\ format.


Segmentation
============

These annotations are used to know the exact geometry of objects in images. It follows the format 
`Common Object in COntext (COCO) <https://cocodataset.org>`__ used by Microsoft.

.. note::
    This annotations file is in ``JSON``\ format.
