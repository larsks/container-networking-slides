import logging
import re
import click
import yaml

from pathlib import Path

from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin
from mdit_py_plugins.footnote import footnote_plugin

re_comment = re.compile(r"<!--(?P<config>.*?)-->", re.DOTALL)


@click.command()
@click.option("--type", "-t", "block_type", default="all")
@click.option("--output", "-o", "outputdir", default=".", type=Path)
@click.option("--list", "-l", "mode_list", is_flag=True)
@click.option("--verbose", "-v", count=True)
@click.argument("inputfiles", type=click.File(mode="r"), nargs=-1)
def main(block_type, inputfiles, verbose, mode_list, outputdir):
    loglevel = [logging.WARNING, logging.INFO, logging.DEBUG][min(verbose, 2)]
    logging.basicConfig(level=loglevel)
    md = (
        MarkdownIt("commonmark", {"breaks": True, "html": True})
        .use(front_matter_plugin)
        .use(footnote_plugin)
        .enable("table")
    )

    seen_files = set()

    for inputfile in inputfiles:
        with inputfile:
            text = inputfile.read()
        tokens = md.parse(text)

        blocks = [token for token in tokens if token.type in ["html_block", "fence"]]
        current_file = None
        current_file_mode = "w"
        config = {}

        for block in blocks:
            if block.type == "html_block":
                if match := re_comment.match(block.content):
                    data = yaml.safe_load(match.group("config"))
                    if not isinstance(data, dict):
                        raise ValueError(data)

                    config.update(data)
                    if "file" in data:
                        current_file = outputdir / data["file"]
                        if current_file in seen_files:
                            current_file_mode = "a"
                        else:
                            logging.info("new file %s", current_file)
                            current_file_mode = "w"
                            seen_files.add(current_file)

            if mode_list:
                continue

            if (
                current_file is not None
                and block.type == "fence"
                and (block_type == "all" or block.info == block_type)
            ):
                with current_file.open(current_file_mode) as fd:
                    fd.write(block.content)
                    current_file = None

    if mode_list:
        print("\n".join(str(path) for path in seen_files))


if __name__ == "__main__":
    main()
