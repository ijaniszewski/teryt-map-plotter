import pandas as pd

import utilities as utils
from teryt_map_plotter import AdminLevel, LevelConfig

DATA_DIR = "data/poland/presidential_results_2025"
VIEW_NAME = "Poland: 2025 Presidential Election: Δ Trzaskowski support (2nd - 1st round)"

def handler_gminy_trzaskowski_change_2025(df_first: pd.DataFrame) -> pd.DataFrame:
    # Load second round CSV
    df_second = pd.read_csv(
        f"{DATA_DIR}/second_round/wyniki_gl_na_kandydatow_po_gminach_w_drugiej_turze_utf8.csv",
        sep=";",
        encoding="utf-8"
    )

    df_first.columns = df_first.columns.str.strip()
    df_second.columns = df_second.columns.str.strip()

    # Clean and fix Warszawa
    df_first = utils.normalize_gminy_data(
        df=df_first,
        teryt_col="TERYT Gminy",
        warszawa_fix=True,
    )
    df_second = utils.normalize_gminy_data(
        df=df_second,
        teryt_col="TERYT Gminy",
        warszawa_fix=True,
    )

    df_first["share_r1"] = utils.to_num(df_first["TRZASKOWSKI Rafał Kazimierz"]) / utils.to_num(df_first["Liczba głosów ważnych oddanych łącznie na wszystkich kandydatów"])
    df_second["share_r2"] = utils.to_num(df_second["TRZASKOWSKI Rafał Kazimierz"]) / utils.to_num(df_second["Liczba głosów ważnych oddanych łącznie na wszystkich kandydatów"])

    merged = pd.merge(
        df_first[["TERYT Gminy", "share_r1"]],
        df_second[["TERYT Gminy", "share_r2"]],
        on="TERYT Gminy"
    )
    merged["trzaskowski_share_change_2025"] = merged["share_r2"] - merged["share_r1"]
    return merged[["TERYT Gminy", "trzaskowski_share_change_2025"]]

LC_PL_2025_TRZASKOWSKI_CHANGE = {
    (AdminLevel.GMINY, VIEW_NAME): LevelConfig(
        csv_path=f"{DATA_DIR}/first_round/wyniki_gl_na_kandydatow_po_gminach_utf8.csv",
        teryt_col="TERYT Gminy",
        value_col="trzaskowski_share_change_2025",
        handler=handler_gminy_trzaskowski_change_2025,
        title=VIEW_NAME,
        preprocessor=utils.preprocess_gminy_geo,
    )
}
