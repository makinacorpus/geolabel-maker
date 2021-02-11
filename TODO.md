# TODO list

## Important

-   Optimize `generate_label()`
-   `Classification`
-   `ObjectDetection` or `YOLO`
-   Crop with rotation (currently not supported, will crop on a regular cartesian grid)
-   Fix `filename` issues.
    - Can occur if the `GeoData` is generated from scratch instead of being loaded from a file from the disk
        - Will raise an error if any methods that need to read / write the data because `filename` is unknown

## Applications

-   U-Net++
-   Change Detection
-   GAN map creation