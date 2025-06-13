import pandas as pd


def load_cleaned_gminy_df(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, sep=";", dtype=str, encoding="utf-8")
    df.columns = df.columns.str.strip()

    # --- Normalize numeric fields ---
    for col in df.columns:
        df[col] = df[col].str.replace(",", ".").str.strip()
        try:
            df[col] = pd.to_numeric(df[col])
        except (ValueError, TypeError):
            continue

    # --- Normalize TERYT (6-digit PKW code) ---
    df["TERYT Gminy"] = (
        pd.to_numeric(df["TERYT Gminy"], errors="coerce")
        .dropna()
        .astype(int)
        .astype(str)
        .str.zfill(6)
    )

    # --- 🏙️ Handle Warszawa dzielnice ---
    # In the shapefile (GEO), Warszawa appears as a single gmina with TERYT 1465011.
    # In the CSV (election results), it's split into 18 districts (dzielnice),
    # each with its own row (TERYT like 146508, 146509, ..., 146514).
    # To align the formats, we sum all rows where Powiat == "Warszawa"
    # and create one combined result with TERYT Gminy = 1465011.
    warszawa_mask = df["Powiat"].str.strip().str.lower() == "warszawa"
    df_wawa = df[warszawa_mask].copy()

    if not df_wawa.empty:
        df_wawa_agg = (
            df_wawa.select_dtypes(include="number").sum(numeric_only=True).to_frame().T
        )
        df_wawa_agg["Gmina"] = "Warszawa"
        df_wawa_agg["Powiat"] = "Warszawa"
        df_wawa_agg["Województwo"] = "mazowieckie"
        df_wawa_agg["TERYT Gminy"] = "146501"

        # Combine with rest
        df_rest = df[~warszawa_mask].copy()
        df = pd.concat([df_rest, df_wawa_agg], ignore_index=True)

    # Final cleanup
    df["TERYT Gminy"] = (
        pd.to_numeric(df["TERYT Gminy"], errors="coerce")
        .dropna()
        .astype(int)
        .astype(str)
        .str.zfill(6)
    )

    return df
