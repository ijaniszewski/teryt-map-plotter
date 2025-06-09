# 🌍 Statistical Map Viewer: Polish Administrative Boundaries & Beyond

A flexible tool to **visualize administrative boundaries** and **merge them with statistical data** (e.g. voter turnout, population, economic indicators). Initially built for Poland, this app supports:

- 🟢 Gmina (commune/municipality)
- 🟠 Powiat (district/county)
- 🔵 Województwo (province/voivodeship)
- ⚪ Country-level overview (e.g. Polska)

But it's designed to **scale to other countries and datasets**.

## ✨ Features
- Visualize boundaries without data ("outline view")
- Merge with statistical datasets via TERYT or other region codes
- Custom preprocessing for regions (e.g. Warszawa aggregation)
- Clean map rendering for analysis or reports
- CLI to explore & plot available configs

---

## 📦 Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 📁 Step 2: Download Shapefiles
Download shapefiles for Polish administrative boundaries from:
[GIS Support – Granice Administracyjne](https://gis-support.pl/baza-wiedzy-2/dane-do-pobrania/granice-administracyjne/)

Each level (gminy, powiaty, etc.) comes as a bundle of files (`.shp`, `.shx`, `.dbf`, etc.). Keep them grouped and named consistently.

Put them in `gis_boundaries/` like this:

```
gis_boundaries/
├── gminy/
│   ├── gminy.shp
│   ├── gminy.dbf
│   └── ...
├── powiaty/
│   ├── powiaty.shp
│   └── ...
├── wojewodztwa/
│   ├── wojewodztwa.shp
│   └── ...
├── polska/
│   ├── polska.shp
│   └── ...
```

---

## 🔄 Step 3: Run the Map Plotter App

Launch the interactive map generator:
```bash
python plot_it.py
```
You'll be prompted to choose:
- A **view** (e.g. voter turnout, boundary-only)
- An **administrative level** (e.g. gmina, powiat, etc.)

The app will:
- Load the matching shapefile
- Optionally merge a dataset
- Plot a colored map

---

## 🌐 Config-Driven Architecture

All views are defined in `LEVEL_CONFIGS`, which merges reusable definitions:
- `process_configs/boundaries.py` – static boundary views
- `process_configs/` election or dataset-specific configs

This keeps logic decoupled from CLI/app logic.

---

## 🔍 Optional: Shapefile Debug/Preview Script

Use this snippet (or `check_boundaries.py`) to test if shapefiles are readable:

```python
import geopandas as gpd
import os
import matplotlib.pyplot as plt

valid_levels = ["gminy", "powiaty", "wojewodztwa", "polska"]
level = "gminy"  # change to your level

if level not in valid_levels:
    raise ValueError(f"Invalid level: {level}. Must be one of {valid_levels}")

shapefile_path = os.path.join("gis_boundaries", level, f"{level}.shp")
gdf = gpd.read_file(shapefile_path)

print(gdf.head())
teryt_candidates = [col for col in gdf.columns if "KOD" in col or "TERYT" in col.upper()]
if teryt_candidates:
    print(f"✅ Found TERYT-like column(s): {teryt_candidates}")
else:
    print("❌ No TERYT column found. Available columns:", gdf.columns)

gdf.plot(edgecolor='black', figsize=(10, 10))
plt.title(f"Polish {level.capitalize()} - Boundary Preview")
plt.axis("off")
plt.show()
```

---

## 📃 Coming Soon
- Upload your own dataset (CSV with region codes)
- Support for more countries
- Color palette customization
- Output maps as images or PDFs

---

## 📊 Example Use Cases
- Elections: visualize turnout or results
- Demographics: population, age structure
- Economics: unemployment, income
- Education, health, infrastructure data

This isn't just a Polish viewer — it's a **framework for geographic statistical visualization**.

---

**Contributors welcome!**