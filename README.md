# TERYT Map Plotter

A small Flask app for coloring Polish administrative boundaries from TERYT-coded data.

It currently supports:

- municipalities, counties, voivodeships, and all of Poland,
- built-in Polish presidential election CSV files from `data/`,
- two-color head-to-head maps between two candidates,
- value-scale candidate support percentage maps,
- turnout maps,
- uploaded CSV files with `teryt;name;value`,
- PNG export from the current map view,
- shareable links for the current map selection.

## Run

```bash
python -m venv venv
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/flask --app app run --debug
```

Then open `http://127.0.0.1:5000`.

The default view opens the 2025 Polish presidential election runoff at county level, with a winner-color comparison between Nawrocki and Trzaskowski.

## Built-In Election Data

The app reads built-in CSV files from `data/` and presents them as:

`Country -> Year -> Election -> Round`

For PKW-style presidential election files it detects candidates automatically and exposes focused map modes instead of every raw numeric column.

## Upload CSV

Uploaded files should be semicolon-separated CSV files and must include one TERYT column:

- `TERYT Gminy`
- `Kod TERYT`
- `TERYT`
- `teryt`

For value-scale maps, include:

```csv
teryt;name;value
020101;Boleslawiec city;10
020102;Boleslawiec rural;20
146501;Warsaw;30
```

Required:

- `teryt`: TERYT code for the selected boundary level: 6 digits for municipalities, 4 for counties, 2 for voivodeships. For the whole country sample, use `000000`.
- `value`: numeric value used for the color scale.

Optional:

- `name`: name shown in the tooltip.
- `color`: CSS color if you want to use the optional uploaded-color mode later.

You can download level-specific templates from the app: municipality, county, voivodeship, and Poland samples.

## Notes

Name-based matching is intentionally not enabled yet. TERYT remains the authoritative key because Polish administrative names are not unique and often differ by spelling or prefix.

Uploads are accepted with a few public-server safeguards:

- uploaded files are stored under random IDs, not original filenames,
- uploaded datasets are not listed globally by `/api/datasets`,
- files are limited to 2 MB, 10,000 rows, and 30 columns,
- CSV must contain usable TERYT rows plus `value` or `color`,
- uploads are not served as static files.

Set `TERYT_UPLOADS_ENABLED=0` to disable uploads completely. Set `TERYT_MAX_UPLOAD_BYTES` to change the request size limit.
