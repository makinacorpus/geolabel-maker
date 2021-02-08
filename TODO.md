# TODO list

## Important

-   Add abstract `Data`class and `DataCollection`
    -   `items` to private `_items`
-   Update `RasterCollection` and `CategoryCollection` class
-   Add abstract `Annotation` or `GroundTruth` labels
-   Update `rescale()` from `Raster`
    -   Add `zoom(...)` method
        -   Rescale with the equivalence resolution = m / pixel from https://wiki.openstreetmap.org/wiki/Zoom_levels
-   Optimize `generate_label()`
-   `Classification`
-   `ObjectDetection` or `YOLO`

## Applications

-   U-Net++
-   Change Detection
-   GAN map creation