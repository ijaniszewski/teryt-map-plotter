from teryt_map_plotter import TerytMapPlotter, AdminLevel
from level_configs import LEVEL_CONFIGS
import click
import os
import inquirer


@click.command()
def main():
    click.echo("#" * 60)
    click.echo("🗺️  TERYT Map Plotter")
    click.echo("-" * 60)

    # Get available values dynamically
    levels = [e.value for e in AdminLevel]
    views = sorted(set(v for (_, v) in LEVEL_CONFIGS.keys()))

    # Choose view
    view_choice = [
        inquirer.List(
            "view", message="Choose what to show", choices=views, default="turnout"
        )
    ]
    view = inquirer.prompt(view_choice)["view"]

    # Choose level
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

    config = LEVEL_CONFIGS.get((level_enum, view))
    if config is None:
        click.echo(f"❌ No config for level={level} and view={view}")
        return

    plotter = TerytMapPlotter(level=level_enum)

    if config.preprocessor:
        plotter.apply_preprocessor(config.preprocessor)

    if config.csv_path:
        plotter.load_data(
            data=config.csv_path, teryt_col=config.teryt_col, handler=config.handler
        )
        plotter.merge(value_col=config.value_col)

    title = config.title or f"{view.title()} by {level.title()}"

    plotter.plot(value_col=config.value_col, title=title)


if __name__ == "__main__":
    main()
