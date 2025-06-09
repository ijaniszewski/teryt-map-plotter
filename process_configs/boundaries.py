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
        title='"Województwo" boudaries',
    ),
    (AdminLevel.POWIATY, view): LevelConfig(
        csv_path=None,
        teryt_col=None,
        value_col=None,
        handler=None,
        title='"Powiat" boudaries',
    ),
    (AdminLevel.GMINY, view): LevelConfig(
        csv_path=None,
        teryt_col=None,
        value_col=None,
        handler=None,
        title='"Gmina" boudaries',
    ),
}
