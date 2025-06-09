# 🗺️ Polish Administrative Boundaries Viewer (Gmina, Powiat, Województwo, and Country)

This tool lets you preview and visualize **Polish administrative boundaries** at multiple levels:
- 🟢 Gmina (commune)
- 🟠 Powiat (district)
- 🔵 Województwo (province)
- ⚪ Country (outline only)

You can use it to:
- Preview boundaries
- Merge with statistical data using TERYT codes
- Plot clean maps for analysis or presentations

## 📦 Step 1: Install Required Libraries
```
pip install geopandas pandas matplotlib
```


## 📁 Step 2: Download Shapefiles
Download shapefiles from
[GIS Support – Granice Administracyjne](https://gis-support.pl/baza-wiedzy-2/dane-do-pobrania/granice-administracyjne/)

Each administrative level (gmina, powiat, etc.) comes as a set of files. Do not separate or rename the files — they must stay together for the map to load properly.

Place the files in `gis_boundaries/` - each administrative level in its own subfolder. For example:
```
gis_boundaries/
├── gminy/
│   ├── gminy.*   ← All files from the gmina dataset
├── powiaty/
│   ├── powiaty.* ← All files from the powiat dataset
├── wojewodztwa/
│   ├── wojewodztwa.* ← All files from the voivodeship dataset
├── polska/
│   ├── polska.*  ← All files for the national outline
```


## 🐍 Step 3: Run the Boundary Viewer Script

Example of loading the shapefile (or just run `check_boundaries.py`):
```python
import geopandas as gpd
import os
import matplotlib.pyplot as plt

# Choose administrative level to load
valid_levels = ["gminy", "powiaty", "wojewodztwa", "polska"]
level = "gminy"  # change to 'powiaty', 'wojewodztwa', or 'polska'

if level not in valid_levels:
    raise ValueError(f"Invalid level: {level}. Must be one of {valid_levels}")

# Build path to shapefile
shapefile_path = os.path.join("gis_boundaries", f"{level}.shp")

# Load the shapefile
gdf = gpd.read_file(shapefile_path)

# Preview data
print(f"First 5 rows of {level}:")
print(gdf.head())

# Try to detect TERYT-like columns
teryt_candidates = [col for col in gdf.columns if "KOD" in col or "TERYT" in col.upper()]
if teryt_candidates:
    print(f"✅ Found TERYT-like column(s): {teryt_candidates}")
else:
    print("❌ No TERYT column found. Available columns:")
    print(gdf.columns)

# Plot the selected level
print(f"🗺️ Plotting {level} map...")
gdf.plot(edgecolor='black', figsize=(10, 10))
plt.title(f"Polish {level.capitalize()} - Boundary Preview")
plt.axis("off")
plt.show()
```