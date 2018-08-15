#!/usr/bin/env python
import urllib.request


detail_map = ["0", "n", "1", "2", ""]
url = "http://wttr.in/{location}?T{detail}"
clean_chain = [
    lambda s: s.decode("utf-8"),
    lambda s: s.split("<pre>")[1],
    lambda s: s.split("</pre>")[0],
    lambda s: s.replace("&quot;", '"')
]

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch weather data via wttr.in"
    )
    parser.add_argument(
        "location",
        metavar="L",
        nargs='?',
        default="",
        type=str,
        help="the target location",
    )
    parser.add_argument(
        "-d",
        "--detail",
        default=0,
        action="count",
        help="the level of detail"
    )
    args = parser.parse_args()
    request = urllib.request.urlopen(url.format(
        location=args.location,
        detail=detail_map[min(args.detail, len(detail_map) - 1)],
    ))
    data = request.read()
    for clean_op in clean_chain:
        data = clean_op(data)
    print(data)
