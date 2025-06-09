"""
CLI tool to plot geospatial maps using TerytMapPlotter and predefined LEVEL_CONFIGS.
This script allows users to interactively select the type of data (view) and
administrative level to visualize using TERYT-coded Polish boundaries.

Run this script with:
    python plot_it.py

Requirements:
    - click
    - inquirer
    - geopandas
    - matplotlib
    - pandas
"""

import os

import click
import inquirer

from level_configs import LEVEL_CONFIGS
from teryt_map_plotter import AdminLevel, TerytMapPlotter


@click.command()
def main():
    """
    CLI entry point for generating TERYT-based administrative maps.

    Guides the user through:
        - Choosing the type of map (view)
        - Selecting the level of administrative boundary
        - Applying preprocessing and merging data
        - Rendering the final plot
    """
    click.echo("#" * 60)
    click.echo("\U0001F5FA\uFE0F  TERYT Map Plotter")
    click.echo("-" * 60)

    # List all available views and levels
    levels = [e.value for e in AdminLevel]
    views = sorted(set(v for (_, v) in LEVEL_CONFIGS.keys()))

    # Prompt user to select view
    view_choice = [
        inquirer.List(
            "view",
            message="Choose what to show",
            choices=views,
            default="turnout",
        )
    ]
    view = inquirer.prompt(view_choice)["view"]

    # Prompt user to select level
    level_choice = [
        inquirer.List(
            "level",
            message="Choose administrative boundaries level (granularity)",
            choices=levels,
            default=os.getenv("AIRFLOW_VAR_LEVEL", "powiaty"),
        )
    ]
    level = inquirer.prompt(level_choice)["level"]
    level_enum = AdminLevel(level)

    # Retrieve configuration
    config = LEVEL_CONFIGS.get((level_enum, view))
    if config is None:
        click.echo(f"\u274C No config for level={level} and view={view}")
        return

    # Initialize plotter
    plotter = TerytMapPlotter(level=level_enum)

    # Apply optional preprocessor
    if config.preprocessor:
        plotter.apply_preprocessor(config.preprocessor)

    # Load and merge data if available
    if config.csv_path:
        plotter.load_data(
            data=config.csv_path,
            teryt_col=config.teryt_col,
            handler=config.handler,
        )
        plotter.merge(value_col=config.value_col)

    # Use custom or fallback title
    title = config.title or f"{view.title()} by {level.title()}"

    # Render the plot
    plotter.plot(value_col=config.value_col, title=title)


if __name__ == "__main__":
    main()
