import logging
import click
from contributors.commands.get_contributors import get_contributors


@click.group(name="semgrep-contributors")
@click.help_option("--help", "-h")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.pass_context
def cli(ctx: click.Context, debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[logging.StreamHandler()],
    )


cli.add_command(cmd=get_contributors)
