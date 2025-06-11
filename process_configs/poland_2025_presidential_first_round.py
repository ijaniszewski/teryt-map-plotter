"""
LC_PL_2025_PE_FIRST defines LevelConfigs for visualizing voter turnout data
from the 2025 Polish Presidential Election (first round).

Each LevelConfig includes:
    - CSV path with election data
    - TERYT column to merge on
    - Handler function to clean and calculate turnout or share
    - Optional preprocessing for geometry
    - Custom title per level

Special handling is included for Warszawa (gmina level) and for national aggregation (Polska).
"""

import pandas as pd

import utilities as utils
from teryt_map_plotter import AdminLevel, LevelConfig

# === CONSTANTS ===
MAIN_TITLE = "Poland: 2025 Presidential Election, first round"
DATA_DIR = "data/poland/presidential_results_2025/first_round"

TURNOUT_VIEW = f"{MAIN_TITLE}: turnout"
INVALID_VOTES_VIEW = f"{MAIN_TITLE}: invalid votes"
TRZASKOWSKI_VIEW = f"{MAIN_TITLE}: Trzaskowski support"

valid_votes_col = "Liczba głosów ważnych oddanych łącznie na wszystkich kandydatów"
invalid_votes_col = "Liczba głosów nieważnych"
eligible_col = "Liczba wyborców uprawnionych do głosowania"
voted_col = (
    "Liczba wyborców, którym wydano karty do głosowania w lokalu "
    "wyborczym oraz w głosowaniu korespondencyjnym (łącznie)"
)
trzaskowski_col = "TRZASKOWSKI Rafał Kazimierz"

# === GMINY HANDLERS ===
def handler_gminy_turnout(df):
    return utils.normalize_gminy_data(
        df,
        teryt_col="TERYT Gminy",
        computed_col_name="turnout",
        computed_fn=lambda d: pd.to_numeric(d[voted_col], errors="coerce") / pd.to_numeric(d[eligible_col], errors="coerce"),
        warszawa_fix=True,
    )

def handler_gminy_invalid(df):
    return utils.normalize_gminy_data(df, "TERYT Gminy", value_col=invalid_votes_col, warszawa_fix=True)

def handler_gminy_invalid_share(df):
    return utils.normalize_gminy_share(df, invalid_votes_col, valid_votes_col, "invalid_share", warszawa_fix=True)

def handler_gminy_trzaskowski_share(df):
    return utils.normalize_gminy_share(df, trzaskowski_col, valid_votes_col, "trzaskowski_share", warszawa_fix=True)

# === POWIATY HANDLERS ===
def handler_powiaty_turnout(df):
    df["TERYT Powiatu"] = pd.to_numeric(df["TERYT Powiatu"], errors="coerce").astype(str).str.zfill(6)
    df["TERYT4"] = df["TERYT Powiatu"].str[:4]
    df["turnout"] = pd.to_numeric(df[voted_col], errors="coerce") / pd.to_numeric(df[eligible_col], errors="coerce")
    return df

def handler_powiaty_share(df, num_col, denom_col, col_name):
    df["TERYT Powiatu"] = pd.to_numeric(df["TERYT Powiatu"], errors="coerce").astype(str).str.zfill(6)
    df["TERYT4"] = df["TERYT Powiatu"].str[:4]
    df[col_name] = pd.to_numeric(df[num_col], errors="coerce") / pd.to_numeric(df[denom_col], errors="coerce")
    return df[["TERYT4", col_name]]

def handler_powiaty_invalid_share(df):
    return handler_powiaty_share(df, invalid_votes_col, valid_votes_col, "invalid_share")

def handler_powiaty_trzaskowski_share(df):
    return handler_powiaty_share(df, trzaskowski_col, valid_votes_col, "trzaskowski_share")

# === WOJEWÓDZTWA HANDLERS ===
def preprocess_wojewodztwa_geo(gdf):
    gdf["JPT_KOD_JE"] = gdf["JPT_NAZWA_"].astype(str)
    return gdf

def handler_wojewodztwa_turnout(df):
    df["Województwo"] = df["Województwo"].str.strip().str.lower()
    df["turnout"] = pd.to_numeric(df[voted_col], errors="coerce") / pd.to_numeric(df[eligible_col], errors="coerce")
    return df

def handler_wojewodztwa_share(df, num_col, denom_col, col_name):
    df["Województwo"] = df["Województwo"].str.strip().str.lower()
    df[col_name] = pd.to_numeric(df[num_col], errors="coerce") / pd.to_numeric(df[denom_col], errors="coerce")
    return df[["Województwo", col_name]]

def handler_wojewodztwa_invalid_share(df):
    return handler_wojewodztwa_share(df, invalid_votes_col, valid_votes_col, "invalid_share")

def handler_wojewodztwa_trzaskowski_share(df):
    return handler_wojewodztwa_share(df, trzaskowski_col, valid_votes_col, "trzaskowski_share")

# === POLSKA HANDLERS ===
def handler_polska_turnout(df):
    df[eligible_col] = pd.to_numeric(df[eligible_col], errors="coerce")
    df[voted_col] = pd.to_numeric(df[voted_col], errors="coerce")
    turnout = df[voted_col].sum() / df[eligible_col].sum()
    return pd.DataFrame({"JPT_KOD_JE": ["0"], "turnout": [turnout]})

def handler_polska_share(df, num_col, denom_col, col_name):
    df[num_col] = pd.to_numeric(df[num_col], errors="coerce")
    df[denom_col] = pd.to_numeric(df[denom_col], errors="coerce")
    share = df[num_col].sum() / df[denom_col].sum()
    return pd.DataFrame({"JPT_KOD_JE": ["0"], col_name: [share]})

def handler_polska_invalid_share(df):
    return handler_polska_share(df, invalid_votes_col, valid_votes_col, "invalid_share")

def handler_polska_trzaskowski_share(df):
    return handler_polska_share(df, trzaskowski_col, valid_votes_col, "trzaskowski_share")

LC_PL_2025_PE_FIRST = {
    # === TURNOUT ===
    (AdminLevel.POLSKA, TURNOUT_VIEW): LevelConfig(
        csv_path=f"{DATA_DIR}/wyniki_gl_na_kandydatow_po_wojewodztwach_utf8.csv",
        teryt_col="JPT_KOD_JE",
        value_col="turnout",
        handler=handler_polska_turnout,
        title=f"{MAIN_TITLE}: voter turnout",
    ),
    (AdminLevel.WOJEWODZTWA, TURNOUT_VIEW): LevelConfig(
        csv_path=f"{DATA_DIR}/wyniki_gl_na_kandydatow_po_wojewodztwach_utf8.csv",
        teryt_col="Województwo",
        value_col="turnout",
        handler=handler_wojewodztwa_turnout,
        preprocessor=preprocess_wojewodztwa_geo,
        title=f"{MAIN_TITLE}: Voter turnout by województwo",
    ),
    (AdminLevel.POWIATY, TURNOUT_VIEW): LevelConfig(
        csv_path=f"{DATA_DIR}/wyniki_gl_na_kandydatow_po_powiatach_utf8.csv",
        teryt_col="TERYT4",
        value_col="turnout",
        handler=handler_powiaty_turnout,
        title=f"{MAIN_TITLE}: Voter turnout by powiat",
    ),
    (AdminLevel.GMINY, TURNOUT_VIEW): LevelConfig(
        csv_path=f"{DATA_DIR}/wyniki_gl_na_kandydatow_po_gminach_utf8.csv",
        teryt_col="TERYT Gminy",
        value_col="turnout",
        handler=handler_gminy_turnout,
        preprocessor=utils.preprocess_gminy_geo,
        title=f"{MAIN_TITLE}: Voter turnout by gmina",
    ),

    # === INVALID VOTES (% SHARE) ===
    (AdminLevel.POLSKA, f"{MAIN_TITLE}: invalid share"): LevelConfig(
        csv_path=f"{DATA_DIR}/wyniki_gl_na_kandydatow_po_wojewodztwach_utf8.csv",
        teryt_col="JPT_KOD_JE",
        value_col="invalid_share",
        handler=handler_polska_invalid_share,
        title=f"{MAIN_TITLE}: % of invalid votes (Polska)",
    ),
    (AdminLevel.WOJEWODZTWA, f"{MAIN_TITLE}: invalid share"): LevelConfig(
        csv_path=f"{DATA_DIR}/wyniki_gl_na_kandydatow_po_wojewodztwach_utf8.csv",
        teryt_col="Województwo",
        value_col="invalid_share",
        handler=handler_wojewodztwa_invalid_share,
        preprocessor=preprocess_wojewodztwa_geo,
        title=f"{MAIN_TITLE}: % of invalid votes by województwo",
    ),
    (AdminLevel.POWIATY, f"{MAIN_TITLE}: invalid share"): LevelConfig(
        csv_path=f"{DATA_DIR}/wyniki_gl_na_kandydatow_po_powiatach_utf8.csv",
        teryt_col="TERYT4",
        value_col="invalid_share",
        handler=handler_powiaty_invalid_share,
        title=f"{MAIN_TITLE}: % of invalid votes by powiat",
    ),
    (AdminLevel.GMINY, f"{MAIN_TITLE}: invalid share"): LevelConfig(
        csv_path=f"{DATA_DIR}/wyniki_gl_na_kandydatow_po_gminach_utf8.csv",
        teryt_col="TERYT Gminy",
        value_col="invalid_share",
        handler=handler_gminy_invalid_share,
        preprocessor=utils.preprocess_gminy_geo,
        title=f"{MAIN_TITLE}: % of invalid votes by gmina",
    ),

    # === TRZASKOWSKI (% SHARE) ===
    (AdminLevel.POLSKA, f"{MAIN_TITLE}: Trzaskowski share"): LevelConfig(
        csv_path=f"{DATA_DIR}/wyniki_gl_na_kandydatow_po_wojewodztwach_utf8.csv",
        teryt_col="JPT_KOD_JE",
        value_col="trzaskowski_share",
        handler=handler_polska_trzaskowski_share,
        title=f"{MAIN_TITLE}: % support for Trzaskowski (Polska)",
    ),
    (AdminLevel.WOJEWODZTWA, f"{MAIN_TITLE}: Trzaskowski share"): LevelConfig(
        csv_path=f"{DATA_DIR}/wyniki_gl_na_kandydatow_po_wojewodztwach_utf8.csv",
        teryt_col="Województwo",
        value_col="trzaskowski_share",
        handler=handler_wojewodztwa_trzaskowski_share,
        preprocessor=preprocess_wojewodztwa_geo,
        title=f"{MAIN_TITLE}: % support for Trzaskowski by województwo",
    ),
    (AdminLevel.POWIATY, f"{MAIN_TITLE}: Trzaskowski share"): LevelConfig(
        csv_path=f"{DATA_DIR}/wyniki_gl_na_kandydatow_po_powiatach_utf8.csv",
        teryt_col="TERYT4",
        value_col="trzaskowski_share",
        handler=handler_powiaty_trzaskowski_share,
        title=f"{MAIN_TITLE}: % support for Trzaskowski by powiat",
    ),
    (AdminLevel.GMINY, f"{MAIN_TITLE}: Trzaskowski share"): LevelConfig(
        csv_path=f"{DATA_DIR}/wyniki_gl_na_kandydatow_po_gminach_utf8.csv",
        teryt_col="TERYT Gminy",
        value_col="trzaskowski_share",
        handler=handler_gminy_trzaskowski_share,
        preprocessor=utils.preprocess_gminy_geo,
        title=f"{MAIN_TITLE}: % support for Trzaskowski by gmina",
    ),
}
