"""
TerytMapPlotter: A flexible class for plotting geospatial data for administrative regions in Poland
using the TERYT coding system. It supports merging external datasets (e.g., election results) with
GeoDataFrames for visualization.

Classes:
    AdminLevel (Enum): Administrative levels in Poland.
    LevelConfig (dataclass): Configuration for plotting a specific administrative level.
    TerytMapPlotter (dataclass): Main class for loading, merging, and plotting TERYT-based maps.

Dependencies:
    - pandas
    - geopandas
    - matplotlib
    - enum
    - os
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional, Union

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

BASE_MAP_DIR = "gis_boundaries"


class AdminLevel(str, Enum):
    """Enumeration of administrative levels in Poland."""
    GMINY = "gminy"
    POWIATY = "powiaty"
    WOJEWODZTWA = "wojewodztwa"
    POLSKA = "polska"


@dataclass
class LevelConfig:
    """Configuration for a specific map level.

    Attributes:
        csv_path (Optional[str]): Path to CSV with additional data.
        teryt_col (Optional[str]): Column in CSV with TERYT codes.
        handler (Optional[Callable]): Function to normalize/prepare data.
        value_col (Optional[str]): Column to visualize on the map.
        title (Optional[str]): Title for the map.
        preprocessor (Optional[Callable]): Function to preprocess GeoDataFrame.
    """
    csv_path: Optional[str]
    teryt_col: Optional[str]
    handler: Optional[Callable[[pd.DataFrame], pd.DataFrame]]
    value_col: Optional[str]
    title: Optional[str]
    preprocessor: Optional[Callable[[gpd.GeoDataFrame], gpd.GeoDataFrame]] = None


@dataclass
class TerytMapPlotter:
    """Class for loading, merging, and visualizing TERYT-based maps in Poland."""

    level: AdminLevel
    shapefile_path: str = None
    teryt_shp_col: str = "JPT_KOD_JE"
    gdf: gpd.GeoDataFrame = field(init=False)

    def __post_init__(self):
        if self.level not in AdminLevel:
            raise ValueError(f"❌ Invalid level: {self.level}")

        # Generate default path if not provided
        if self.shapefile_path is None:
            self.shapefile_path = os.path.join(
                BASE_MAP_DIR, self.level.value, f"{self.level.value}.shp"
            )

        self.gdf = gpd.read_file(self.shapefile_path).to_crs(epsg=4326)

    def apply_preprocessor(
        self, preprocessor: Callable[[gpd.GeoDataFrame], gpd.GeoDataFrame]
    ):
        """Apply a custom preprocessing function to the GeoDataFrame."""
        self.gdf = preprocessor(self.gdf)

    def load_data(
        self,
        data: Union[str, pd.DataFrame],
        teryt_col: str,
        handler: Callable[[pd.DataFrame], pd.DataFrame],
    ):
        """
        Load and preprocess external data (e.g., voting data).

        Args:
            data (str or pd.DataFrame): Path to CSV or a DataFrame.
            teryt_col (str): Column name with TERYT codes.
            handler (Callable): Function that cleans and returns a processed DataFrame.
        """
        df = (
            pd.read_csv(data, sep=";", dtype=str, encoding="utf-8")
            if isinstance(data, str)
            else data.copy()
        )
        df.columns = df.columns.str.strip()
        try:
            for col in df.columns:
                df[col] = df[col].str.replace(",", ".").str.strip()
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    continue
        except Exception as e:
            print(f"⚠️ Failed to load voting data: {e}")

        df = handler(df)
        self.df = df
        self.teryt_data_col = teryt_col

    def merge(self, value_col: str):
        """
        Merge the processed data with the shapefile based on TERYT code.

        Args:
            value_col (str): Column name with values to visualize.

        Raises:
            ValueError: If the column is missing or unmatched regions exist.
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
        """
        Plot the map, optionally with data coloring.

        Args:
            value_col (str, optional): Name of the column to visualize.
            title (str): Title for the plot.
            cmap (str): Matplotlib colormap name.

        Raises:
            ValueError: If specified column does not exist.
        """
        if not hasattr(self, "merged"):
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
