"""
LEVEL_CONFIGS combines various LevelConfig definitions for use with TerytMapPlotter.

It merges administrative boundary-only views and the 2025 Polish Presidential Election (first round)
turnout data. Each key is a tuple of (AdminLevel, view), and each value is a LevelConfig object
defining how to load, merge, and visualize the data.
"""

from process_configs.boundaries import LC_BOUNDARIES
from process_configs.poland_2025_pesidential_first_round import LC_PL_2025_PE_FIRST

LEVEL_CONFIGS = {
    **LC_BOUNDARIES,
    **LC_PL_2025_PE_FIRST,
}