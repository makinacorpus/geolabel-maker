
## Set-Up

#### Inputs

To create your labels and annotations, you need:

```
data
├── categories
│   ├── buildings.json
│   └── vegetation.json
├── images
│   ├── 1843_5174_08_CC46.tif
│   └── 1844_5173_08_CC46.tif
└── categories.json
```

- `images/` : The folder containing the images to be labeled.
- `categories/` : The folder containing the different vectors per category (e.g. `buildings.json` is a set of polygons corresponding to some buildings)
- `categories.json` : The file mapping the different categories (e.g. buildings, vegetation etc.) to their location, ids and RGB color.

Example of the `categories.json` file:

```json
{
    "category_1": {
        "id": 0,
        "file": "categories/vegetation.json",
        "color": [0, 150, 0]
    },
    "category_2": {
        "id": 1,
        "file": "categories/buildings.json",
        "color": [255, 255, 255]
    }
}
```