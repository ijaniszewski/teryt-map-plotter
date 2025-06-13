# 🗘️ TerytMapPlotter: Statistical Maps by Administrative Boundaries (Poland-first, world-ready)

A lightweight Python tool for mapping **statistical data** across **administrative units**, based on **TERYT codes**. Originally built for Polish elections, it supports:

* 🟢 Gminy (municipalities)
* 🟠 Powiaty (counties/districts)
* 🔵 Województwa (provinces)
* ⚪ Country-level (e.g. Poland as a whole)

This tool takes **any metric** mapped to a **TERYT code** and visualizes it — automatically matching to boundaries and aggregating as needed.

---

## ✅ What You Need

To generate a map, you only need:

```python
{"TERYT_ID": value}
```

Where:

* `TERYT_ID` is a code for a gmina (6-digit), powiat (4-digit), or województwo (2-digit)
* `value` is whatever you want to show: turnout, support %, population, etc.

---

## 🧠 Why It Just Works

* 🌟 Automatically matches your codes to the correct boundaries
* 🏙️ **Fixes Warsaw**: Aggregates 18 PKW "dzielnice" into a single gmina, matching the shapefile
* 🧲 Aggregates gmina-level data to powiat or województwo if needed (via mean by default)
* 🧩 Supports custom aggregation handlers (e.g. median, weighted average)

---

## 🖼️ Example: Voter Turnout by Gmina

```python
from teryt_map_plotter import TerytMapPlotter, AdminLevel
import utilities as utils
import os

# Load and clean raw CSV
base_data_dir = "data/poland/2025/presidential_elections/first_round"
csv_path = os.path.join(base_data_dir, "wyniki_gl_na_kandydatow_po_gminach_utf8.csv")

df = utils.load_cleaned_gminy_df(csv_path)

# Calculate turnout
df["turnout"] = df["Liczba wyborców, którym wydano karty do głosowania w lokalu wyborczym oraz w głosowaniu korespondencyjnym (łącznie)"] / df["Liczba wyborców uprawnionych do głosowania"]

# Convert to dict {TERYT: value}
turnout_dict = df.set_index("TERYT Gminy")["turnout"].to_dict()

# Plot at gmina level
plotter = TerytMapPlotter(
    level=AdminLevel.GMINY,
    teryt_dict=turnout_dict,
    value_col="turnout"
)

plotter.plot_boundaries("Voter Turnout by Gmina")
```

---

## 🔄 Aggregate Automatically

If you pass gmina-level data but want to see the result at powiat or województwo level, just change the level:

```python
plotter = TerytMapPlotter(
    level=AdminLevel.POWIATY,
    teryt_dict=turnout_dict,
    value_col="turnout"
)

plotter.plot_boundaries("Avg Turnout by Powiat")
```

By default, it will average all gminas within each powiat.

You can pass a custom `handler=` function to use median, min, max, or any other aggregation.

---

## 🔍 Visualizing Without Data

Want just the outlines? No problem:

```python
plotter = TerytMapPlotter(level=AdminLevel.GMINY)
plotter.plot_boundaries("Administrative Boundaries Only")
```

---

## 🚀 Getting Started

1. **Install dependencies**:

```bash
pip install -r requirements.txt
```

2. **Download shapefiles** from:
   [https://gis-support.pl/baza-wiedzy-2/dane-do-pobrania/granice-administracyjne/](https://gis-support.pl/baza-wiedzy-2/dane-do-pobrania/granice-administracyjne/)

   ✅ **Only one shapefile needed**

   Place the gmina-level shapefiles in the following folder:

```
gis_boundaries/
└── gminy/
    ├── gminy.shp
    ├── gminy.dbf
    ├── gminy.shx
    └── ...
```

3. **Run your script** (e.g., to plot turnout)

---

## 📚 Example Use Cases

* 🗳️ Election turnout, invalid votes, candidate support
* 🤝 Demographic analysis
* 📈 Economic indicators (GDP, unemployment)
* 🏥 Access to public services
* 🔺 Any dataset tied to regional codes

---

**Built in Python. Works with any GeoDataFrame. Ready to be adapted to other countries.**
