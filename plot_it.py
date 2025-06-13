from teryt_map_plotter import TerytMapPlotter, AdminLevel  # adjust import if needed
import os
import utilities as utils  # assumes you have load_cleaned_gminy_df() there

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
