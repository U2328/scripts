#!/usr/bin/env python
from __future__ import annotations
from typing import List, Optional
from dataclasses import dataclass, field
import re


class MDToC_Exception(Exception):
    ...


@dataclass
class Section:
    name: str
    sub_sections: List[Section] = field(default_factory=list)
    parent: Optional[Section] = None

    def __repr__(self):
        return f"<{self.name}:{self.sub_sections}>"

    def add_subsection(self, name):
        section = Section(name=name, parent=self)
        self.sub_sections.append(section)
        return section

    def get_linked_entry(self):
        link = self.name.lower().replace(" ", "-")
        return f"- [{self.name}](#{link})"

    def get_unlinked_entry(self):
        return f'- {self.name}'


def parse_sections(file, depth=3, heading="# Table of contents:"):
    sections = []
    last_section = None
    last_depth = 1
    for i, line in enumerate(file):

        # if it ain't a heading, skip it
        if line[0] != "#":
            continue

        if line[:-1] == heading:
            raise MDToC_Exception(
                "Found heading that would collide with" +
                f" the ToC heading on line {i}."
            )

        # get the raw caption name
        raw_caption = line.replace("#", "")
        # determin the section depth by the difference
        section_depth = len(line) - len(raw_caption)
        if section_depth > depth:
            continue

        # clean up the caption name
        caption = raw_caption.strip()
        if section_depth > 1:
            try:
                if section_depth - 1 == last_depth:
                    last_section = last_section.add_subsection(caption)
                elif section_depth + 1 == last_depth:
                    last_section = last_section.parent.parent.add_subsection(caption)
                elif section_depth == last_depth:
                    last_section = last_section.parent.add_subsection(caption)
                else:
                    raise AttributeError()
            except AttributeError as e:
                # If this shizzle skedidled something done did fucked up
                depth_diff = section_depth - last_depth - 1
                plural = "s" if depth_diff > 1 else ""
                raise MDToC_Exception(
                    f"Found illegal section level at line {i+1},"
                    f"this section is {depth_diff} level{plural} to deep."
                )
        else:
            last_section = Section(name=caption)
            sections.append(last_section)
        last_depth = section_depth
    return sections


def generate_toc(sections, linked=False):
    toc = []
    for section in sections:
        toc.append(
            section.get_linked_entry()
            if linked else
            section.get_unlinked_entry()
        )
        toc += [f" {x}" for x in generate_toc(section.sub_sections, linked)]
    return toc


def inject_toc(file, toc, marker=None, heading="# Table of contents:"):
    file.seek(0)
    text = file.read()
    toc_string = heading + "\n" + "\n".join(toc) + "\n\n"
    if marker:
        if marker in text:
            new_text = re.sub(marker + "\n", toc_string, text)
        else:
            raise MDToC_Exception("Couldn't find the given marker.")
    else:
        new_text = toc_string + text

    file.seek(0)
    file.write(new_text)


def main(infile, depth, linked, marker, outfile, verbose, heading):
    if verbose:
        print("Gather sections...", end="")
    sections = parse_sections(infile, depth, heading)
    if verbose:
        print("done")
        print("Generating ToC from sections...", end="")
    toc = generate_toc(sections, linked)
    if verbose:
        print("done")
        print("Injecting ToC into file...", end="")
    inject_toc(outfile or infile, toc, marker, heading)
    if verbose:
        print("done")


if __name__ == "__main__":
    import argparse

    def gt_zero(s):
        i = int(s)
        if i > 0:
            return i
        else:
            print("The given depth must be > 0.")
            exit()

    parser = argparse.ArgumentParser(description="Inject ToC into md-file")
    parser.add_argument(
        "source",
        metavar="S",
        type=argparse.FileType("r+"),
        help="the file to source from",
    )
    parser.add_argument(
        "-l", "--linked", action="store_true", help="make ToC entries linked"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="display processing state"
    )
    parser.add_argument(
        "-d",
        "--depth",
        metavar="D",
        type=gt_zero,
        default=3,
        help="make ToC entries linked",
    )
    parser.add_argument(
        "-m",
        "--marker",
        metavar="M",
        type=str,
        default=None,
        help="the location to add the ToC",
    )
    parser.add_argument(
        "-H",
        "--heading",
        metavar="H",
        type=str,
        default="# Table of contents:",
        help="header of the ToC",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="O",
        type=argparse.FileType("r+"),
        default=None,
        help="the location to add the ToC",
    )
    args = parser.parse_args()
    try:
        main(
            args.source,
            args.depth,
            args.linked,
            args.marker,
            args.output,
            args.verbose,
            args.heading,
        )
    except MDToC_Exception as e:
        print(e.args[0])
    finally:
        args.source.close()
        if args.output:
            args.output.close()
