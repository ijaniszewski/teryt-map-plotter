from typing import Callable, Optional

import pandas as pd


# === HELPERS ===
def preprocess_gminy_geo(gdf: pd.DataFrame) -> pd.DataFrame:
    # Pad to 7 digits and slice to match CSV's 6-digit TERYT
    gdf["JPT_KOD_JE"] = gdf["JPT_KOD_JE"].astype(str).str.zfill(7).str[:6]
    # ✅ remove last digit to match 6-digit CSV TERYT
    return gdf

def normalize_gminy_data(
    df: pd.DataFrame,
    teryt_col: str,
    value_col: Optional[str] = None,
    computed_col_name: Optional[str] = None,
    computed_fn: Optional[Callable[[pd.DataFrame], pd.Series]] = None,
    warszawa_fix: bool = False,
    teryt_len: int = 6,
) -> pd.DataFrame:
    df = df.copy()
    df[teryt_col] = (
        pd.to_numeric(df[teryt_col], errors="coerce")
        .dropna()
        .astype(int)
        .astype(str)
        .str.zfill(teryt_len)
    )

    if warszawa_fix:
        df["Powiat"] = df["Powiat"].str.strip().str.lower()
        warszawa_mask = df["Powiat"] == "warszawa"
        df_wawa = df[warszawa_mask].copy()
        if not df_wawa.empty:
            numeric_cols = df_wawa.select_dtypes(include="number").columns.tolist()
            df_wawa_agg = df_wawa[numeric_cols].sum().to_frame().T
            df_wawa_agg["Gmina"] = "Warszawa"
            df_wawa_agg["Powiat"] = "warszawa"
            df_wawa_agg["Województwo"] = "mazowieckie"
            df_wawa_agg[teryt_col] = "146501"
            df = pd.concat([df[~warszawa_mask], df_wawa_agg], ignore_index=True)

    df[teryt_col] = pd.to_numeric(df[teryt_col], errors="coerce").astype("Int64").astype(str).str.zfill(teryt_len)

    if computed_col_name and computed_fn:
        df[computed_col_name] = computed_fn(df)
        return df[[teryt_col, computed_col_name]]
    elif value_col:
        return df[[teryt_col, value_col]]
    else:
        # No value extracted – return full cleaned DataFrame
        return df

def normalize_gminy_share(df, numerator_col, denominator_col, share_name, warszawa_fix=False):
    return normalize_gminy_data(
        df=df,
        teryt_col="TERYT Gminy",
        computed_col_name=share_name,
        computed_fn=lambda d: pd.to_numeric(d[numerator_col], errors="coerce") /
                              pd.to_numeric(d[denominator_col], errors="coerce"),
        warszawa_fix=warszawa_fix,
    )

def to_num(col):
    return pd.to_numeric(col.astype(str).str.replace(",", ".").str.strip(), errors="coerce")