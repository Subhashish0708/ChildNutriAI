# Dataset Folder

This folder contains:
- Child Images
- Anthropometric Dataset
- Sample Test Images

The dataset will be used for training and testing the AI model for child malnutrition detection.

## Folder structure

```
dataset
│
├── images
│      ├── normal
│      ├── moderate
│      └── severe
│
├── anthropometric
│      child_health_data.csv
│
├── sample_images
│
├── README.md
│
└── dataset_info.txt
```

- **images/** — training images sorted by class (`normal`, `moderate`, `severe`). Empty for now (`.gitkeep` placeholders); add real photos as they're collected.
- **anthropometric/child_health_data.csv** — health parameters (Age, Height, Weight, MUAC, Gender) with the diagnosis label for each child.
- **sample_images/** — held-out images for testing model predictions, kept separate from the training set.
- **dataset_info.txt** — dataset name, data sources, and the classes/parameters used.
