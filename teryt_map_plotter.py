import os
from collections import defaultdict
from enum import Enum
from typing import Callable, Dict, Optional

import geopandas as gpd
import matplotlib.pyplot as plt

BASE_MAP_DIR = "gis_boundaries"


class AdminLevel(str, Enum):
    GMINY = "gminy"
    POWIATY = "powiaty"
    WOJEWODZTWA = "wojewodztwa"
    POLSKA = "polska"


class TerytMapPlotter:
    """
    Plots statistical maps using gmina-level shapefile,
    aggregating geometries as needed for higher levels.

    Args:
        level (AdminLevel): Target level (gminy, powiaty, etc.)
        teryt_dict (Optional[Dict[str, float]]): Dictionary {TERYT: value}.
        value_col (str): Column name to store in GeoDataFrame.
        handler (Optional[Callable]): Optional aggregation function.
    """

    def __init__(
        self,
        level: AdminLevel,
        teryt_dict: Optional[Dict[str, float]] = None,
        value_col: str = "value",
        handler: Optional[Callable[[Dict[str, float]], Dict[str, float]]] = None,
    ):
        self.level = level
        self.teryt_dict = teryt_dict
        self.value_col = value_col
        self.handler = handler
        self.teryt_shp_col = "JPT_KOD_JE"

        self.shapefile_path = os.path.join(BASE_MAP_DIR, "gminy", "gminy.shp")
        self._load_shapefile()

        if self.level != AdminLevel.GMINY:
            self._aggregate_geometry()

        if self.teryt_dict:
            self._apply_values()

    def _load_shapefile(self):
        self.gdf = gpd.read_file(self.shapefile_path).to_crs(epsg=4326)
        self.gdf["TERYT6"] = self.gdf[self.teryt_shp_col].astype(str).str[:6]

    def _aggregate_geometry(self):
        key_len = self._get_key_length()
        self.gdf["agg_key"] = self.gdf["TERYT6"].str[:key_len]
        self.gdf = self.gdf.dissolve(by="agg_key", as_index=False)

    def _apply_values(self):
        if self.handler:
            final_dict = self.handler(self.teryt_dict)
        else:
            target_len = self._get_key_length()
            final_dict = self._default_aggregate(self.teryt_dict, target_len)

        if self.level == AdminLevel.GMINY:
            self.gdf[self.value_col] = self.gdf["TERYT6"].map(final_dict)
        else:
            self.gdf[self.value_col] = self.gdf["agg_key"].map(final_dict)

    @staticmethod
    def _infer_teryt_length(teryt_dict: Dict[str, float]) -> int:
        return len(next(iter(teryt_dict)))

    def _get_key_length(self) -> int:
        return {
            AdminLevel.GMINY: 6,
            AdminLevel.POWIATY: 4,
            AdminLevel.WOJEWODZTWA: 2,
            AdminLevel.POLSKA: 0,
        }.get(self.level, 6)

    @staticmethod
    def _default_aggregate(
        teryt_dict: Dict[str, float], target_len: int
    ) -> Dict[str, float]:
        groups = defaultdict(list)
        for teryt, val in teryt_dict.items():
            key = str(teryt)[:target_len]
            groups[key].append(val)
        return {k: sum(v) / len(v) for k, v in groups.items()}

    def plot_boundaries(
        self,
        title: str = "Administrative Boundaries",
        value_col: Optional[str] = None,
        fig: Optional[plt.Figure] = None,
        ax: Optional[plt.Axes] = None,
    ):
        user_supplied_axes = fig is not None and ax is not None

        if not user_supplied_axes:
            fig, ax = plt.subplots(figsize=(12, 12))

        column = value_col or self.value_col

        if column and column in self.gdf.columns:
            self.gdf.plot(
                column=column,
                cmap="OrRd",
                linewidth=0.1,
                edgecolor="black",
                legend=True,
                ax=ax,
            )
            ax.set_title(title, fontsize=16)
        else:
            self.gdf.plot(edgecolor="black", linewidth=0.3, ax=ax)
            ax.set_title(f"{title} (no data)", fontsize=16)

        ax.axis("off")

        if user_supplied_axes:
            return fig, ax
        else:
            plt.tight_layout()
            plt.subplots_adjust(top=0.92)
            plt.show()
