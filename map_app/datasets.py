from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


TERYT_COLUMNS = ("TERYT Gminy", "Kod TERYT", "TERYT", "teryt")
NAME_COLUMNS = {
    6: ("Gmina", "Powiat", "Województwo"),
    4: ("Powiat", "Województwo"),
    2: ("Województwo",),
}
VALID_VOTES_COLUMNS = (
    "Liczba glosow waznych oddanych lacznie na wszystkich kandydatow",
    "Liczba głosów ważnych oddanych łącznie na wszystkich kandydatów",
)
ELIGIBLE_COLUMNS = (
    "Liczba wyborcow uprawnionych do glosowania",
    "Liczba wyborców uprawnionych do głosowania",
)
BALLOTS_COLUMNS = (
    "Liczba wyborcow, ktorym wydano karty do glosowania w lokalu wyborczym oraz w glosowaniu korespondencyjnym (lacznie)",
    "Liczba wyborców, którym wydano karty do głosowania w lokalu wyborczym oraz w głosowaniu korespondencyjnym (łącznie)",
)


@dataclass(frozen=True)
class DatasetInfo:
    id: str
    name: str
    path: Path
    source: str
    facets: dict[str, str]


class DatasetCatalog:
    def __init__(self, data_dir: str | Path, upload_dir: str | Path):
        self.data_dir = Path(data_dir).resolve()
        self.upload_dir = Path(upload_dir).resolve()
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def list(self, include_uploads: bool = False) -> list[dict[str, Any]]:
        datasets = []
        roots = [("built-in", self.data_dir)]
        if include_uploads:
            roots.append(("uploaded", self.upload_dir))
        for source, root in roots:
            if not root.exists():
                continue
            for path in sorted(root.rglob("*.csv")):
                info = self._info_for(path, root, source)
                datasets.append(
                    {
                        "id": info.id,
                        "name": info.name,
                        "source": source,
                        "facets": info.facets,
                    }
                )
        return datasets

    def resolve(self, dataset_id: str) -> DatasetInfo:
        for source, root in (("built-in", self.data_dir), ("uploaded", self.upload_dir)):
            prefix = f"{source}:"
            if dataset_id.startswith(prefix):
                rel = Path(dataset_id.removeprefix(prefix))
                path = (root / rel).resolve()
                if path.exists() and root.resolve() in path.parents:
                    return self._info_for(path, root, source)
        raise FileNotFoundError(dataset_id)

    def profile(self, dataset_id: str) -> dict[str, Any]:
        info = self.resolve(dataset_id)
        df = self._load(info.path)
        candidates = self._candidate_columns(df)
        modes = []
        if len(candidates) >= 2:
            modes.append({"id": "head_to_head", "label": "Head-to-head winner"})
        if candidates:
            modes.append({"id": "candidate_share", "label": "Candidate support"})
        if self._first_existing(df, ELIGIBLE_COLUMNS) and self._first_existing(df, BALLOTS_COLUMNS):
            modes.append({"id": "turnout", "label": "Turnout"})
        if "value" in {col.lower() for col in df.columns}:
            modes.append({"id": "uploaded_value", "label": "Value scale"})
        if "color" in {col.lower() for col in df.columns}:
            modes.append({"id": "custom_color", "label": "Uploaded colors"})

        return {
            "id": info.id,
            "name": info.name,
            "rows": len(df),
            "facets": info.facets,
            "candidates": candidates,
            "modes": modes,
            "suggested_level": self._suggested_level(df) if info.source == "uploaded" else None,
            "preferred_mode": self._preferred_upload_mode(df) if info.source == "uploaded" else None,
        }

    def values(
        self,
        dataset_id: str,
        mode: str,
        level: str,
        candidate: str | None = None,
        candidate_a: str | None = None,
        candidate_b: str | None = None,
    ) -> dict[str, Any]:
        info = self.resolve(dataset_id)
        df = self._load(info.path)
        target_len = {"gminy": 6, "powiaty": 4, "wojewodztwa": 2, "polska": 0}[level]

        if mode == "head_to_head":
            candidates = self._candidate_columns(df)
            candidate_a = candidate_a or (candidates[0] if candidates else None)
            candidate_b = candidate_b or (candidates[1] if len(candidates) > 1 else None)
            if not candidate_a or not candidate_b:
                raise ValueError("Choose two candidates for head-to-head mode")
            features = self._head_to_head(df, candidate_a, candidate_b, target_len)
            legend = {"type": "diverging", "left": candidate_b, "right": candidate_a}
        elif mode == "candidate_share":
            candidate = candidate or (self._candidate_columns(df)[0] if self._candidate_columns(df) else None)
            if not candidate:
                raise ValueError("Choose a candidate")
            features = self._candidate_share(df, candidate, target_len)
            legend = {"type": "sequential", "label": f"{candidate} support"}
        elif mode == "turnout":
            features = self._turnout(df, target_len)
            legend = {"type": "sequential", "label": "Turnout"}
        elif mode == "uploaded_value":
            features = self._uploaded_value(df, target_len)
            legend = {"type": "sequential", "label": "Value scale"}
        elif mode == "custom_color":
            features = self._custom_colors(df, target_len)
            legend = {"type": "custom", "label": "Uploaded colors"}
        else:
            raise ValueError(f"Unknown mode: {mode}")

        return {
            "features": features,
            "stats": self._stats(features),
            "legend": legend,
        }

    def save_upload(self, file_storage) -> str:
        filename = Path(file_storage.filename or "dataset.csv").name
        if not filename.lower().endswith(".csv"):
            raise ValueError("Only CSV files are supported")

        target = self.upload_dir / f"{uuid.uuid4().hex}.csv"
        file_storage.save(target)
        try:
            self._validate_upload(target)
        except Exception:
            target.unlink(missing_ok=True)
            raise
        return self._id_for(target, self.upload_dir, "uploaded")

    def sample_csv(self, level: str) -> str:
        target_len = {"gminy": 6, "powiaty": 4, "wojewodztwa": 2, "polska": 0}[level]
        rows = self._reference_rows(target_len)
        lines = ["teryt;name;value"]
        for index, (teryt, name) in enumerate(rows[:12], start=1):
            lines.append(f"{teryt};{name};{index * 10}")
        lines.append("")
        return "\n".join(lines)

    def _load(self, path: Path) -> pd.DataFrame:
        df = pd.read_csv(path, sep=";", dtype=str, encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].str.strip()

        teryt_col = self._teryt_column(df)
        for col in df.columns:
            if col == teryt_col or col.lower() == "color":
                continue
            numeric = pd.to_numeric(df[col].str.replace(",", ".", regex=False), errors="coerce")
            if numeric.notna().sum() > 0:
                df[col] = numeric

        df["teryt_input"] = df[teryt_col].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
        df["teryt"] = (
            pd.to_numeric(df[teryt_col], errors="coerce")
            .astype("Int64")
            .astype(str)
            .str.zfill(6)
        )
        df = df[df["teryt"].str.fullmatch(r"\d{6}", na=False)].copy()
        return self._merge_warsaw(df)

    def _validate_upload(self, path: Path) -> None:
        if path.stat().st_size > 2 * 1024 * 1024:
            raise ValueError("CSV is too large. Keep uploads under 2 MB.")
        df = self._load(path)
        if df.empty:
            raise ValueError("CSV has no usable TERYT rows.")
        if len(df) > 10_000:
            raise ValueError("CSV has too many rows. Limit is 10,000.")
        if len(df.columns) > 30:
            raise ValueError("CSV has too many columns. Limit is 30.")
        lower_columns = {col.lower() for col in df.columns}
        if "value" not in lower_columns and "color" not in lower_columns:
            raise ValueError("CSV must include at least a 'value' or 'color' column.")

    def _merge_warsaw(self, df: pd.DataFrame) -> pd.DataFrame:
        if "Powiat" not in df.columns:
            return df
        warsaw_mask = df["Powiat"].astype(str).str.strip().str.lower() == "warszawa"
        warsaw = df[warsaw_mask]
        if warsaw.empty:
            return df

        numeric = warsaw.select_dtypes(include="number").sum(numeric_only=True).to_frame().T
        merged = {col: "" for col in df.columns}
        merged.update(numeric.iloc[0].to_dict())
        merged["teryt"] = "146501"
        merged["Gmina"] = "Warszawa"
        merged["Powiat"] = "Warszawa"
        if "Województwo" in df.columns:
            merged["Województwo"] = "mazowieckie"
        return pd.concat([df[~warsaw_mask], pd.DataFrame([merged])], ignore_index=True)

    def _head_to_head(
        self, df: pd.DataFrame, candidate_a: str, candidate_b: str, target_len: int
    ) -> dict[str, dict[str, Any]]:
        for candidate_name in (candidate_a, candidate_b):
            if candidate_name not in df.columns:
                raise ValueError(f"Unknown candidate: {candidate_name}")

        groups = self._sum_columns(df, [candidate_a, candidate_b], target_len)
        names = self._names_by_key(df, target_len)
        features = {}
        for key, sums in groups.items():
            total = sums[candidate_a] + sums[candidate_b]
            if total <= 0:
                continue
            margin = (sums[candidate_a] - sums[candidate_b]) / total * 100
            winner = candidate_a if margin >= 0 else candidate_b
            features[key] = {
                "value": margin,
                "winner": winner,
                "margin": abs(margin),
                "name": names.get(key),
                "candidate_a": candidate_a,
                "candidate_b": candidate_b,
                "share_a": sums[candidate_a] / total * 100,
                "share_b": sums[candidate_b] / total * 100,
            }
        return features

    def _candidate_share(self, df: pd.DataFrame, candidate: str, target_len: int) -> dict[str, dict[str, Any]]:
        valid_votes = self._first_existing(df, VALID_VOTES_COLUMNS)
        if not valid_votes or candidate not in df.columns:
            raise ValueError("This file does not contain the columns needed for candidate support")
        values = self._aggregate_ratio(df, df[candidate], df[valid_votes], target_len)
        names = self._names_by_key(df, target_len)
        return {
            key: {"value": value, "name": names.get(key), "candidate": candidate}
            for key, value in values.items()
        }

    def _turnout(self, df: pd.DataFrame, target_len: int) -> dict[str, dict[str, Any]]:
        eligible = self._first_existing(df, ELIGIBLE_COLUMNS)
        ballots = self._first_existing(df, BALLOTS_COLUMNS)
        if not eligible or not ballots:
            raise ValueError("This file does not contain the columns needed for turnout")
        values = self._aggregate_ratio(df, df[ballots], df[eligible], target_len)
        names = self._names_by_key(df, target_len)
        return {key: {"value": value, "name": names.get(key)} for key, value in values.items()}

    def _custom_colors(self, df: pd.DataFrame, target_len: int) -> dict[str, dict[str, Any]]:
        color_col = next((col for col in df.columns if col.lower() == "color"), None)
        if not color_col:
            raise ValueError("Uploaded color mode requires a 'color' column")
        value_col = next((col for col in df.columns if col.lower() == "value"), None)
        label_col = next((col for col in df.columns if col.lower() in {"name", "nazwa", "label"}), None)
        names = self._names_by_key(df, target_len)
        features = {}
        for _, row in df.iterrows():
            key = self._upload_key(row, target_len)
            value = row[value_col] if value_col else None
            features[key] = {
                "value": float(value) if value is not None and pd.notna(value) else None,
                "name": row[label_col] if label_col and pd.notna(row[label_col]) else names.get(key),
                "color": row[color_col],
            }
        return features

    def _uploaded_value(self, df: pd.DataFrame, target_len: int) -> dict[str, dict[str, Any]]:
        value_col = next((col for col in df.columns if col.lower() == "value"), None)
        if not value_col:
            raise ValueError("Value scale mode requires a 'value' column")
        label_col = next((col for col in df.columns if col.lower() in {"name", "nazwa", "label"}), None)
        names = self._names_by_key(df, target_len)
        raw: dict[str, list[float]] = {}
        labels: dict[str, str] = {}
        for _, row in df.iterrows():
            value = row[value_col]
            if value is None or pd.isna(value) or not math.isfinite(float(value)):
                continue
            key = self._upload_key(row, target_len)
            raw.setdefault(key, []).append(float(value))
            if label_col and pd.notna(row[label_col]) and str(row[label_col]).strip():
                labels.setdefault(key, str(row[label_col]))
        return {
            key: {
                "value": sum(items) / len(items),
                "name": labels.get(key) or names.get(key),
            }
            for key, items in raw.items()
        }

    def _aggregate_ratio(
        self, df: pd.DataFrame, numerator: pd.Series, denominator: pd.Series, target_len: int
    ) -> dict[str, float]:
        groups: dict[str, list[float]] = {}
        for teryt, num, den in zip(df["teryt"], numerator, denominator):
            if pd.isna(num) or pd.isna(den) or float(den) == 0:
                continue
            key = "PL" if target_len == 0 else str(teryt)[:target_len]
            if key not in groups:
                groups[key] = [0.0, 0.0]
            groups[key][0] += float(num)
            groups[key][1] += float(den)
        return {key: num / den * 100 for key, (num, den) in groups.items() if den}

    def _sum_columns(self, df: pd.DataFrame, columns: list[str], target_len: int) -> dict[str, dict[str, float]]:
        groups: dict[str, dict[str, float]] = {}
        for _, row in df.iterrows():
            key = "PL" if target_len == 0 else str(row["teryt"])[:target_len]
            groups.setdefault(key, {col: 0.0 for col in columns})
            for col in columns:
                if pd.notna(row[col]):
                    groups[key][col] += float(row[col])
        return groups

    def _upload_key(self, row: pd.Series, target_len: int) -> str:
        if target_len == 0:
            return "PL"
        raw = str(row.get("teryt_input", "")).strip()
        if raw.isdigit() and len(raw) <= target_len:
            return raw.zfill(target_len)
        return str(row["teryt"])[:target_len]

    def _names_by_key(self, df: pd.DataFrame, target_len: int) -> dict[str, str]:
        if target_len == 0:
            return {"PL": "Poland"}

        columns = [col for col in NAME_COLUMNS.get(target_len, ()) if col in df.columns]
        names = {}
        for _, row in df.iterrows():
            key = str(row["teryt"])[:target_len]
            parts = [str(row[col]) for col in columns if pd.notna(row[col]) and str(row[col]).strip()]
            if parts and key not in names:
                names[key] = ", ".join(parts)
        return names

    def _candidate_columns(self, df: pd.DataFrame) -> list[str]:
        valid_votes = self._first_existing(df, VALID_VOTES_COLUMNS)
        if not valid_votes:
            return []
        candidates = []
        after_valid_votes = False
        for col in df.columns:
            if col == valid_votes:
                after_valid_votes = True
                continue
            if after_valid_votes and pd.api.types.is_numeric_dtype(df[col]):
                candidates.append(col)
        return candidates

    def _stats(self, features: dict[str, dict[str, Any]]) -> dict[str, float | int | None]:
        numbers = [
            float(item["value"])
            for item in features.values()
            if item.get("value") is not None and math.isfinite(float(item["value"]))
        ]
        if not numbers:
            colored_count = sum(1 for item in features.values() if item.get("color"))
            if colored_count:
                return {"count": colored_count, "min": None, "max": None, "mean": None}
        return {
            "count": len(numbers),
            "min": min(numbers) if numbers else None,
            "max": max(numbers) if numbers else None,
            "mean": sum(numbers) / len(numbers) if numbers else None,
        }

    def _suggested_level(self, df: pd.DataFrame) -> str:
        raw_codes = df["teryt_input"].astype(str).str.strip()
        if raw_codes.eq("000000").all():
            return "polska"
        lengths = raw_codes[raw_codes.str.fullmatch(r"\d+", na=False)].str.len()
        if lengths.empty:
            return "gminy"
        common_len = int(lengths.mode().iloc[0])
        return {2: "wojewodztwa", 4: "powiaty", 6: "gminy"}.get(common_len, "gminy")

    def _preferred_upload_mode(self, df: pd.DataFrame) -> str:
        lower_columns = {col.lower() for col in df.columns}
        if "color" in lower_columns:
            return "custom_color"
        if "value" in lower_columns:
            return "uploaded_value"
        return "uploaded_value"

    def _teryt_column(self, df: pd.DataFrame) -> str:
        for col in TERYT_COLUMNS:
            if col in df.columns:
                return col
        raise ValueError("CSV must contain a TERYT column")

    def _first_existing(self, df: pd.DataFrame, names: tuple[str, ...]) -> str | None:
        return next((name for name in names if name in df.columns), None)

    def _info_for(self, path: Path, root: Path, source: str) -> DatasetInfo:
        return DatasetInfo(
            id=self._id_for(path, root, source),
            name=self._name_for(path, root, source),
            path=path,
            source=source,
            facets=self._facets_for(path, root, source),
        )

    def _id_for(self, path: Path, root: Path, source: str) -> str:
        return f"{source}:{path.relative_to(root).as_posix()}"

    def _reference_rows(self, target_len: int) -> list[tuple[str, str]]:
        if target_len == 0:
            return [("000000", "Poland")]
        rows: dict[str, str] = {}
        for path in sorted(self.data_dir.rglob("*.csv")):
            try:
                df = self._load(path)
            except Exception:
                continue
            rows.update(self._names_by_key(df, target_len))
            if len(rows) >= 12:
                break
        return sorted(rows.items())

    def _name_for(self, path: Path, root: Path, source: str) -> str:
        facets = self._facets_for(path, root, source)
        if source == "built-in":
            return " / ".join(
                part
                for part in [
                    facets.get("country"),
                    facets.get("year"),
                    facets.get("election"),
                    facets.get("round"),
                ]
                if part
            )
        return f"Uploaded CSV {path.stem[:8]}"

    def _facets_for(self, path: Path, root: Path, source: str) -> dict[str, str]:
        if source == "uploaded":
            return {
                "country": "Uploaded",
                "year": "Custom",
                "election": "CSV upload",
                "round": "Uploaded dataset",
            }

        parts = path.relative_to(root).parts
        country = {"poland": "Poland"}.get(parts[0], parts[0].title()) if len(parts) > 0 else "Unknown"
        year = parts[1] if len(parts) > 1 else "Unknown"
        election = (
            parts[2].replace("_", " ").title()
            if len(parts) > 2
            else "Unknown election"
        )
        round_name = (
            {"first_round": "First round", "second_round": "Second round"}.get(parts[3], parts[3].replace("_", " ").title())
            if len(parts) > 3
            else "Unknown round"
        )
        return {"country": country, "year": year, "election": election, "round": round_name}
