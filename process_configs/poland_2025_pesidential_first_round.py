from teryt_map_plotter import AdminLevel, LevelConfig
import pandas as pd

MAIN_TITLE = "Poland: 2025 Presidential Election, first round"
DATA_DIR = "data/poland/presidential_results_2025/first_round"

eligible_col = "Liczba wyborców uprawnionych do głosowania"
voted_col = (
    "Liczba wyborców, którym wydano karty do głosowania w lokalu "
    "wyborczym oraz w głosowaniu korespondencyjnym (łącznie)"
)


def handler_powiaty_turnover(df: pd.DataFrame) -> pd.DataFrame:
    df["TERYT Powiatu"] = (
        pd.to_numeric(df["TERYT Powiatu"], errors="coerce")
        .dropna()
        .astype(int)
        .astype(str)
        .str.zfill(6)
    )
    df["TERYT4"] = df["TERYT Powiatu"].str[:4]

    df["turnout"] = pd.to_numeric(df[voted_col], errors="coerce") / pd.to_numeric(
        df[eligible_col], errors="coerce"
    )
    return df


def handler_wojewodztwa_turnover(df: pd.DataFrame) -> pd.DataFrame:
    df["Województwo"] = df["Województwo"].str.strip().str.lower()

    df["turnout"] = pd.to_numeric(df[voted_col], errors="coerce") / pd.to_numeric(
        df[eligible_col], errors="coerce"
    )

    return df


def preprocess_wojewodztwa_geo(gdf: pd.DataFrame) -> pd.DataFrame:
    gdf["JPT_KOD_JE"] = gdf["JPT_NAZWA_"].astype(str)
    return gdf


def handler_polska_turnover(df: pd.DataFrame) -> pd.DataFrame:
    # NOTE!
    # The result may slightly differ from official figures, as it is
    # calculated based on regional (województwo-level) data and not all
    # individual votes (e.g. votes from abroad, ships, etc. are not included).

    df[eligible_col] = pd.to_numeric(df[eligible_col], errors="coerce")
    df[voted_col] = pd.to_numeric(df[voted_col], errors="coerce")

    total_eligible = df[eligible_col].sum()
    total_voted = df[voted_col].sum()

    turnout = total_voted / total_eligible if total_eligible else None

    # Create single-row DataFrame with dummy key for merging
    return pd.DataFrame(
        {
            "JPT_KOD_JE": ["0"],  # 👈 to match shapefile
            "turnout": [turnout],
        }
    )


def handler_gminy_turnover(df: pd.DataFrame) -> pd.DataFrame:
    merge_key_csv = "TERYT Gminy"

    # Step 1: Clean and normalize TERYT from CSV
    df[merge_key_csv] = (
        pd.to_numeric(df[merge_key_csv], errors="coerce")
        .dropna()
        .astype(int)
        .astype(str)
        .str.zfill(6)  # ensure 6-digit base
    )

    # 🏙️ Step 2: Special-case Warszawa handling
    # In the shapefile (GEO), Warszawa appears as a single gmina with TERYT 1465011.
    # In the CSV (election results), it's split into 18 districts (dzielnice),
    # each with its own row (TERYT like 146508, 146509, ..., 146514).
    # To align the formats, we sum all rows where Powiat == "Warszawa"
    # and create one combined result with TERYT Gminy = 1465011.

    df["Powiat"] = df["Powiat"].str.strip().str.lower()
    warszawa_mask = df["Powiat"] == "warszawa"
    df_wawa = df[warszawa_mask].copy()

    if not df_wawa.empty:
        numeric_cols = df_wawa.select_dtypes(include="number").columns.tolist()
        df_wawa_agg = df_wawa[numeric_cols].sum().to_frame().T

        # Add categorical metadata
        df_wawa_agg["Gmina"] = "Warszawa"
        df_wawa_agg["Powiat"] = "warszawa"
        df_wawa_agg["Województwo"] = "mazowieckie"
        df_wawa_agg["TERYT Gminy"] = "146501"

        # Merge back
        df = pd.concat([df[~warszawa_mask], df_wawa_agg], ignore_index=True)

    # Re-clean TERYT
    df[merge_key_csv] = (
        pd.to_numeric(df["TERYT Gminy"], errors="coerce")
        .dropna()
        .astype(int)
        .astype(str)
        .str.zfill(6)
    )

    df["turnout"] = pd.to_numeric(df[voted_col], errors="coerce") / pd.to_numeric(
        df[eligible_col], errors="coerce"
    )

    return df


def preprocess_gminy_geo(gdf: pd.DataFrame) -> pd.DataFrame:
    # Pad to 7 digits and slice to match CSV's 6-digit TERYT
    gdf["JPT_KOD_JE"] = gdf["JPT_KOD_JE"].astype(str).str.zfill(7).str[:6]
    # ✅ remove last digit to match 6-digit CSV TERYT
    return gdf


LC_PL_2025_PE_FIRST = {
    (AdminLevel.POLSKA, f"{MAIN_TITLE}: turnout"): LevelConfig(
        csv_path=f"{DATA_DIR}/wyniki_gl_na_kandydatow_po_wojewodztwach_utf8.csv",
        teryt_col="JPT_KOD_JE",
        value_col="turnout",
        handler=handler_polska_turnover,
        title=f"{MAIN_TITLE}: voter turnout",
    ),
    (AdminLevel.WOJEWODZTWA, f"{MAIN_TITLE}: turnout"): LevelConfig(
        csv_path=f"{DATA_DIR}/wyniki_gl_na_kandydatow_po_wojewodztwach_utf8.csv",
        teryt_col="Województwo",
        value_col="turnout",
        handler=handler_wojewodztwa_turnover,
        preprocessor=preprocess_wojewodztwa_geo,
        title=f'{MAIN_TITLE}: Voter turnout by "województwo"',
    ),
    (AdminLevel.POWIATY, f"{MAIN_TITLE}: turnout"): LevelConfig(
        csv_path=f"{DATA_DIR}/wyniki_gl_na_kandydatow_po_powiatach_utf8.csv",
        teryt_col="TERYT4",
        value_col="turnout",
        handler=handler_powiaty_turnover,
        title='Voter turnout by "powiat"',
    ),
    (AdminLevel.GMINY, f"{MAIN_TITLE}: turnout"): LevelConfig(
        csv_path=f"{DATA_DIR}/wyniki_gl_na_kandydatow_po_gminach_utf8.csv",
        teryt_col="TERYT Gminy",
        value_col="turnout",
        handler=handler_gminy_turnover,
        preprocessor=preprocess_gminy_geo,
        title=f'{MAIN_TITLE}: Voter turnout by "gmina"',
    ),
}
