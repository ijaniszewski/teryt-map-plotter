import pandas as pd

import utilities as utils  # ✅ Use shared helpers
from teryt_map_plotter import AdminLevel, LevelConfig

DATA_DIR = "data/poland/presidential_results_2020"
VIEW_NAME = "Poland: 2020 Presidential Election: Δ Trzaskowski support (2nd - 1st round)"

def handler_gminy_trzaskowski_change_2020(df_first: pd.DataFrame) -> pd.DataFrame:
    # Load second round CSV
    df_second = pd.read_csv(
        f"{DATA_DIR}/second_round/wyniki_gl_na_kand_po_gminach_utf8 2.csv",
        sep=";",
        encoding="utf-8"
    )

    # Clean headers
    df_first.columns = df_first.columns.str.strip()
    df_second.columns = df_second.columns.str.strip()

    # Normalize TERYT and aggregate Warszawa
    # Clean and fix Warszawa
    df_first = utils.normalize_gminy_data(
        df=df_first,
        teryt_col="Kod TERYT",
        warszawa_fix=True,
    )

    df_second = utils.normalize_gminy_data(
        df=df_second,
        teryt_col="Kod TERYT",
        warszawa_fix=True,
    )

    # Compute share of votes for Trzaskowski in both rounds
    df_first["share_r1"] = utils.to_num(df_first["Rafał Kazimierz TRZASKOWSKI"]) / utils.to_num(df_first["Liczba głosów ważnych oddanych łącznie na wszystkich kandydatów"])
    df_second["share_r2"] = utils.to_num(df_second["Rafał Kazimierz TRZASKOWSKI"]) / utils.to_num(df_second["Liczba głosów ważnych oddanych łącznie na wszystkich kandydatów"])

    # Merge and compute change
    merged = pd.merge(
        df_first[["Kod TERYT", "share_r1"]],
        df_second[["Kod TERYT", "share_r2"]],
        on="Kod TERYT"
    )
    merged["trzaskowski_share_change_2020"] = merged["share_r2"] - merged["share_r1"]

    return merged.rename(columns={"Kod TERYT": "TERYT Gminy"})[["TERYT Gminy", "trzaskowski_share_change_2020"]]

LC_PL_2020_TRZASKOWSKI_CHANGE = {
    (AdminLevel.GMINY, VIEW_NAME): LevelConfig(
        csv_path=f"{DATA_DIR}/first_round/wyniki_gl_na_kand_po_gminach_utf8.csv",
        teryt_col="TERYT Gminy",
        value_col="trzaskowski_share_change_2020",
        handler=handler_gminy_trzaskowski_change_2020,
        title=VIEW_NAME,
        preprocessor=utils.preprocess_gminy_geo,
    )
}
