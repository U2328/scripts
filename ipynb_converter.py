#!/usr/bin/env python
import json
from functools import reduce
from collections import namedtuple


cell_formatters = {
    "markdown": {
        "md": lambda s: "".join(s) + "\n",
    },
    "code": {
        "md": lambda s: "\n```python\n" + "".join(s) + "\n```\n",
        "py": lambda s: "".join(s),
    },
}

legal_file_extensions = ("md", "py")
Cell = namedtuple("Cell", ["descriptor", "source"])


def main(in_file, out_file, out_format):
    data = map(
        lambda obj: Cell(obj["cell_type"], obj["source"]),
        json.load(in_file)["cells"]
    )
    out_string = reduce(
        lambda acc, cell:
        acc + (
            cell_formatters[cell.descriptor].get(
                out_format,
                lambda s: ""
            )(cell.source)
            if not cell.source == []
            else ""
        ),
        data,
        "",
    )
    out_file.write(out_string)


if __name__ == "__main__":
    import argparse
    import os

    Target = namedtuple("Target", ["file", "extension"])

    def get_file(accessor):
        def inner(path):
            f = open(path, accessor)
            name, extension = os.path.splitext(path)
            return Target(f, extension[1:])

        return inner

    parser = argparse.ArgumentParser(
        description="Convert an iPython notebook into different formats."
    )
    parser.add_argument(
        "source",
        metavar="S",
        type=get_file("r"),
        help="the file to source from"
    )
    parser.add_argument(
        "target",
        metavar="T",
        type=get_file("w"),
        help="the file to write to"
    )
    parser.add_argument(
        "-f",
        "--format",
        metavar="F",
        default=None,
        choices=legal_file_extensions,
        help="format to convert to",
    )
    parser.add_argument(
        "-F",
        "--force",
        action="store_true",
        help="disregard input files extension"
    )
    args = parser.parse_args()
    try:
        if args.source.extension != "ipynb" and not args.force:
            print(
                "Illegal file extension, must be" +
                f"'.ipynb' but is '{args.source.extension}'."
            )
        else:
            main(
                args.source.file,
                args.target.file,
                args.format or args.target.extension
            )
    except Exception as e:
        raise e
    finally:
        args.source.file.close()
        args.target.file.close()
