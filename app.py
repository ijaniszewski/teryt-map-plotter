import os
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request

from map_app import BoundaryStore, DatasetCatalog
from map_app.geometry import LEVELS


BASE_DIR = Path(__file__).parent


def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("TERYT_MAX_UPLOAD_BYTES", 2 * 1024 * 1024))
    app.config["UPLOADS_ENABLED"] = os.environ.get("TERYT_UPLOADS_ENABLED", "1") == "1"

    boundaries = BoundaryStore(BASE_DIR / "gis_boundaries" / "gminy" / "gminy.shp")
    datasets = DatasetCatalog(BASE_DIR / "data", BASE_DIR / "uploads")

    @app.get("/")
    def index():
        return render_template("index.html", levels=LEVELS)

    @app.get("/api/datasets")
    def api_datasets():
        return jsonify({"datasets": datasets.list()})

    @app.get("/api/datasets/<path:dataset_id>")
    def api_dataset(dataset_id):
        return jsonify(datasets.profile(dataset_id))

    @app.get("/api/map")
    def api_map():
        level = request.args.get("level", "gminy")
        dataset_id = request.args.get("dataset")
        mode = request.args.get("mode")
        if level not in LEVELS:
            return jsonify({"error": "Unknown administrative level"}), 400

        payload = {"stats": None, "legend": None}
        features = None
        if dataset_id and mode:
            result = datasets.values(
                dataset_id=dataset_id,
                mode=mode,
                level=level,
                candidate=request.args.get("candidate"),
                candidate_a=request.args.get("candidate_a"),
                candidate_b=request.args.get("candidate_b"),
            )
            features = result["features"]
            boundary_keys = set(boundaries.for_level(level)["teryt"])
            features = {key: value for key, value in features.items() if key in boundary_keys}
            payload["stats"] = stats_for(features)
            payload["legend"] = result["legend"]

        payload["geojson"] = boundaries.geojson(level, features)
        return jsonify(payload)

    @app.get("/api/sample-csv")
    def api_sample_csv():
        level = request.args.get("level", "gminy")
        if level not in LEVELS:
            return jsonify({"error": "Unknown administrative level"}), 400
        return Response(
            datasets.sample_csv(level),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename=teryt_{level}_sample.csv"},
        )

    @app.post("/api/uploads")
    def api_uploads():
        if not app.config["UPLOADS_ENABLED"]:
            return jsonify({"error": "Uploads are disabled on this server"}), 403
        upload = request.files.get("file")
        if not upload:
            return jsonify({"error": "Missing file"}), 400
        try:
            dataset_id = datasets.save_upload(upload)
            profile = datasets.profile(dataset_id)
        except Exception as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify(profile), 201

    return app


def stats_for(features: dict[str, dict]):
    numbers = [
        float(item["value"])
        for item in features.values()
        if item.get("value") is not None
    ]
    return {
        "count": len(numbers),
        "min": min(numbers) if numbers else None,
        "max": max(numbers) if numbers else None,
        "mean": sum(numbers) / len(numbers) if numbers else None,
    }


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
