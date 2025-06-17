import os

import matplotlib.pyplot as plt  # needed to create optional fig/ax

import utilities as utils
from teryt_map_plotter import AdminLevel, TerytMapPlotter

# -----------------------------------------------------------------------
# Step 1: Define path to PKW gmina-level election results
# -----------------------------------------------------------------------

base_data_dir = "data/poland/2025/presidential_elections/first_round"
csv_gminy_path = os.path.join(
    base_data_dir, "wyniki_gl_na_kandydatow_po_gminach_utf8.csv"
)

# -----------------------------------------------------------------------
# Step 2: Load and normalize the raw PKW data
# -----------------------------------------------------------------------
# This helper function:
# - Converts comma-separated numbers to floats
# - Strips spaces
# - Ensures all TERYT codes are zero-padded strings
# - Merges all 18 Warsaw dzielnice into a single row (TERYT Gminy = 146501)
#   since Warsaw is a single gmina in the shapefile
df = utils.load_cleaned_gminy_df(csv_gminy_path)

# -----------------------------------------------------------------------
# Step 3: Calculate turnout metric (can be replaced with anything else)
# -----------------------------------------------------------------------
# We now calculate the percentage of voters who actually cast a ballot
eligible = "Liczba wyborców uprawnionych do głosowania"
voted = (
    "Liczba wyborców, którym wydano karty do głosowania w lokalu wyborczym "
    "oraz w głosowaniu korespondencyjnym (łącznie)"
)

df["turnout"] = df[voted] / df[eligible]

# -----------------------------------------------------------------------
# Step 4: Convert DataFrame into a TERYT → value dictionary
# -----------------------------------------------------------------------
# TerytMapPlotter expects a dictionary like:
# {
#     "146501": 0.612,  # TERYT code (6-digit or 4-digit) : value to plot
#     ...
# }
turnout_dict = df.set_index("TERYT Gminy")["turnout"].to_dict()

# -----------------------------------------------------------------------
# Step 5: Initialize the plotter and generate a map
# -----------------------------------------------------------------------
# Here we plot at the GMINA level directly using the 6-digit TERYT codes.
# The plotter will internally match these to the shapefile (which uses 7-digit codes)
# by comparing only the first 6 digits.

lvl = AdminLevel.WOJEWODZTWA

plotter = TerytMapPlotter(level=lvl, teryt_dict=turnout_dict, value_col="turnout")

# OPTIONAL: Provide fig/ax for customization
customize = True  # <- Set to True if you want to control figure size, font, layout, or save to file

if customize:
    # Manually create matplotlib figure and axes with a custom size
    fig, ax = plt.subplots(figsize=(14, 10))

    # Pass fig and ax to the plotter to take full control of the appearance
    plotter.plot_boundaries(
        f"Voter Turnout by {lvl.value.capitalize()}", fig=fig, ax=ax
    )

    # Customize the title appearance (e.g., larger font size)
    ax.set_title("Custom Title Fontsize", fontsize=20)

    # Adjust layout and save the figure to file
    plt.tight_layout()
    plt.savefig("custom_turnout_map.png", dpi=300)

else:
    # Default behavior: plot with internal fig/ax and automatic layout/show
    plotter.plot_boundaries(f"Voter Turnout by {lvl.value.capitalize()}")

# -----------------------------------------------------------------------
# OPTIONAL: Plot aggregated data at POWIAT level using a custom handler
# -----------------------------------------------------------------------
# If you want to visualize the same data at a higher level (e.g. powiats),
# just change the `level` to AdminLevel.POWIATY and either:
# - let the plotter aggregate the gminas for you (default = mean)
# - OR define your own aggregation logic using a `handler` function

# Example of custom aggregation: take MIN turnout per powiat
# from collections import defaultdict
# import numpy as np

# def min_by_powiat(teryt_dict):
#     groups = defaultdict(list)
#     for teryt, val in teryt_dict.items():
#         groups[str(teryt)[:4]].append(val)  # first 4 digits = powiat
#     return {k: float(np.min(v)) for k, v in groups.items()}

# plotter = TerytMapPlotter(
#     level=AdminLevel.POWIATY,
#     teryt_dict=turnout_dict,
#     value_col="turnout",
#     handler=min_by_powiat
# )

# plotter.plot_boundaries("Minimum Voter Turnout by Powiat")
