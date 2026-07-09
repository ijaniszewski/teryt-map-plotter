from functools import lru_cache
from pathlib import Path

import geopandas as gpd


LEVELS = {
    "gminy": {"label": "Municipalities", "key_len": 6},
    "powiaty": {"label": "Counties", "key_len": 4},
    "wojewodztwa": {"label": "Voivodeships", "key_len": 2},
    "polska": {"label": "Poland", "key_len": 0},
}


class BoundaryStore:
    def __init__(self, shapefile_path: str | Path):
        self.shapefile_path = Path(shapefile_path)

    @lru_cache(maxsize=1)
    def _base(self):
        gdf = gpd.read_file(self.shapefile_path)
        gdf["teryt"] = gdf["JPT_KOD_JE"].astype(str).str[:6]
        gdf["name"] = gdf["JPT_NAZWA_"].astype(str)
        return gdf[["teryt", "name", "geometry"]]

    @lru_cache(maxsize=4)
    def for_level(self, level: str):
        if level not in LEVELS:
            raise ValueError(f"Unknown level: {level}")

        key_len = LEVELS[level]["key_len"]
        gdf = self._base().copy()

        if key_len == 6:
            out = gdf
        else:
            gdf["teryt"] = "PL" if key_len == 0 else gdf["teryt"].str[:key_len]
            out = gdf.dissolve(by="teryt", as_index=False)
            out["name"] = out["teryt"].map(lambda code: "Polska" if code == "PL" else code)

        out = out.to_crs(epsg=2180)
        out["geometry"] = out.geometry.simplify(500 if level == "gminy" else 250, preserve_topology=True)
        return out.to_crs(epsg=4326)

    def geojson(self, level: str, features: dict[str, dict] | None = None):
        gdf = self.for_level(level).copy()
        features = features or {}
        gdf["value"] = gdf["teryt"].map(lambda key: features.get(key, {}).get("value"))
        gdf["data_name"] = gdf["teryt"].map(lambda key: features.get(key, {}).get("name"))
        gdf["display_name"] = gdf["data_name"].fillna(gdf["name"])
        gdf["winner"] = gdf["teryt"].map(lambda key: features.get(key, {}).get("winner"))
        gdf["margin"] = gdf["teryt"].map(lambda key: features.get(key, {}).get("margin"))
        gdf["candidate"] = gdf["teryt"].map(lambda key: features.get(key, {}).get("candidate"))
        gdf["candidate_a"] = gdf["teryt"].map(lambda key: features.get(key, {}).get("candidate_a"))
        gdf["candidate_b"] = gdf["teryt"].map(lambda key: features.get(key, {}).get("candidate_b"))
        gdf["share_a"] = gdf["teryt"].map(lambda key: features.get(key, {}).get("share_a"))
        gdf["share_b"] = gdf["teryt"].map(lambda key: features.get(key, {}).get("share_b"))
        gdf["color"] = gdf["teryt"].map(lambda key: features.get(key, {}).get("color"))
        gdf["has_value"] = gdf["value"].notna()
        return gdf.to_json(drop_id=True)
