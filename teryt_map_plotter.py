from dataclasses import dataclass, field
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from typing import Union, Optional, Callable
from enum import Enum
import os

BASE_MAP_DIR = "gis_boundaries"


class AdminLevel(str, Enum):
    # Administrative boundaries
    GMINY = "gminy"
    POWIATY = "powiaty"
    WOJEWODZTWA = "wojewodztwa"
    POLSKA = "polska"


@dataclass
class LevelConfig:
    csv_path: Optional[str]  # None if boundaries-only
    teryt_col: Optional[str]  # None if not merging
    handler: Optional[Callable[[pd.DataFrame], pd.DataFrame]]
    value_col: Optional[str]  # None if just plotting boundaries
    title: Optional[str]  # Title of generated map
    preprocessor: Optional[Callable[[gpd.GeoDataFrame], gpd.GeoDataFrame]] = None


@dataclass
class TerytMapPlotter:
    level: AdminLevel
    shapefile_path: str = None
    teryt_shp_col: str = "JPT_KOD_JE"
    gdf: gpd.GeoDataFrame = field(init=False)

    def __post_init__(self):
        if self.level not in AdminLevel:
            raise ValueError(f"❌ Invalid level: {self.level}")

        # Auto-generate shapefile path if not provided
        if self.shapefile_path is None:
            self.shapefile_path = os.path.join(
                BASE_MAP_DIR, self.level.value, f"{self.level.value}.shp"
            )

        self.gdf = gpd.read_file(self.shapefile_path).to_crs(epsg=4326)

    def apply_preprocessor(
        self, preprocessor: Callable[[gpd.GeoDataFrame], gpd.GeoDataFrame]
    ):
        self.gdf = preprocessor(self.gdf)

    def load_data(
        self,
        data: Union[str, pd.DataFrame],
        teryt_col: str,
        handler: Callable[[pd.DataFrame], pd.DataFrame],
    ):
        """
        Load election data (CSV or DataFrame), and apply a custom TERYT/data handler.
        The handler must return a modified DataFrame with normalized TERYT and target column(s).
        """
        df = (
            pd.read_csv(data, sep=";", dtype=str, encoding="utf-8")
            if isinstance(data, str)
            else data.copy()
        )
        df.columns = df.columns.str.strip()
        try:
            # Fix decimal separators and convert to numeric safely
            for col in df.columns:
                df[col] = df[col].str.replace(",", ".").str.strip()
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    continue
        except Exception as e:
            print(f"⚠️ Failed to load voting data: {e}")
        df = handler(df)  # <–– user applies any logic: turnout calc, teryt norm etc.
        self.df = df
        self.teryt_data_col = teryt_col

    def merge(self, value_col: str):
        """
        Merge election data with shapefile and ensure the value_col exists.
        """

        self.merged = self.gdf.merge(
            self.df,
            left_on=self.teryt_shp_col,
            right_on=self.teryt_data_col,
            how="left",
        )

        if value_col not in self.merged.columns:
            raise ValueError(f"🛑 Column '{value_col}' not found after merge.")

        missing = self.merged[self.merged[value_col].isna()]
        if not missing.empty:
            print("❌ Missing values:")
            print(missing[[self.teryt_shp_col]].head())
            raise ValueError(f"🛑 {len(missing)} unmatched regions in shapefile.")

    def plot(self, value_col: str = None, title: str = "Map", cmap: str = "OrRd"):
        if not hasattr(self, "merged"):
            # Allow fallback to raw shapefile for 'boundaries' plots
            self.merged = self.gdf.copy()
        if value_col:
            if value_col not in self.merged.columns:
                raise ValueError(f"🛑 Missing column '{value_col}' for plotting.")

        fig, ax = plt.subplots(figsize=(12, 12))

        if value_col:
            self.merged.plot(
                column=value_col,
                cmap=cmap,
                linewidth=0.1,
                edgecolor="black",
                legend=True,
                ax=ax,
            )
        else:
            self.merged.plot(edgecolor="black", linewidth=0.3, ax=ax)

        ax.set_title(title, fontsize=16)
        ax.axis("off")
        plt.tight_layout()
        plt.subplots_adjust(top=0.92)
        plt.show()
