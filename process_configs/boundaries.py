"""
LC_BOUNDARIES defines configurations for visualizing only administrative boundaries (no data overlay)
in Poland at different levels of granularity using TERYT codes.

Each LevelConfig in this module sets:
    - No CSV data (boundaries-only)
    - No TERYT merge
    - No value column
    - No handler or preprocessing
    - Custom title for each map

Use case: structural/geographic visualization without any statistical overlays.
"""

from teryt_map_plotter import AdminLevel, LevelConfig

view = "boundaries"

LC_BOUNDARIES = {
    (AdminLevel.POLSKA, view): LevelConfig(
        csv_path=None,
        teryt_col=None,
        value_col=None,
        handler=None,
        title="Polska",
    ),
    (AdminLevel.WOJEWODZTWA, view): LevelConfig(
        csv_path=None,
        teryt_col=None,
        value_col=None,
        handler=None,
        title='"Województwo" boundaries',
    ),
    (AdminLevel.POWIATY, view): LevelConfig(
        csv_path=None,
        teryt_col=None,
        value_col=None,
        handler=None,
        title='"Powiat" boundaries',
    ),
    (AdminLevel.GMINY, view): LevelConfig(
        csv_path=None,
        teryt_col=None,
        value_col=None,
        handler=None,
        title='"Gmina" boundaries',
    ),
}