import json
import re
import math
from dateutil import parser as datetime_parser
from abc import ABCMeta, abstractmethod
import multiprocessing as mp


__all__ = (
    "MissingKeyError",
    "DataContainer",
    "JSON_DataContainer",
    "Filter",
    "fill_template"
)


# == Exceptions
class MissingKeyError(Exception):
    ...


# == Classes
class DataContainer(metaclass=ABCMeta):
    __slots__ = ('_data')
    _available_containers = {}

    @classmethod
    def make_container(cls, type_str, *args, **kwargs):
        return cls._available_containers[type_str](*args, **kwargs)

    def __init_subclass__(cls, file_type, **kwargs):
        super().__init_subclass__(**kwargs)
        DataContainer._available_containers[file_type] = cls

    def __getitem__(self, key):
        return self.get_value(key)

    @abstractmethod
    def get_value(self, key):
        ...


class JSON_DataContainer(DataContainer, file_type="json"):
    def __init__(self, file):
        if isinstance(file, str):
            with open(file, "r") as f:
                self._data = json.load(f)
        else:
            self._data = json.load(file)

    def get_value(self, key, default=None):
        assert isinstance(key, str), "Key musst be of type str..."
        key_chain = key.split('.')
        current = self._data
        for key_chain_link in key_chain:
            try:
                current = current[key_chain_link]
            except KeyError as e:
                raise MissingKeyError(e)
        return current


class Filter:
    _filters = {}
    _cache = {}
    _filter_re = re.compile(r"^(?P<func>[^()]+)(?:\((?P<args>.*)\))?$")
    _arg_re = re.compile(r"(?P<arg>[^(),]+(?:\([^()]*\))?)")
    escape_sequences = {
        '\\n': '\n',
    }

    @classmethod
    def apply_filters(cls, value, filters):
        if filters:
            for filter_string in filters:
                    value = cls._apply_filter(value, filter_string)
        return str(value)

    @classmethod
    def _apply_filter(cls, value, filter_string):
        cache_key = str(value) + "___" + filter_string
        if cache_key in cls._cache:
            return cls._cache[cache_key]
        elif filter_string != "":
            try:
                    func, args = cls._parse_filter(filter_string)
                    value = cls._filters[func](value, *args)
                    cls._cache[cache_key] = value
                    return value
            except KeyError as e:
                    raise SyntaxError(f"unkown filter \"{func}\"")
        else:
            raise SyntaxError("illegal filter syntax")

    @classmethod
    def _parse_filter(cls, filter_string):
        match = cls._filter_re.fullmatch(filter_string)
        func = match.group("func")
        args = []
        if match.group("args"):
            args.extend(
                x.group("arg")
                for x in cls._arg_re.finditer(match.group("args"))
            )
        return func, args

    @classmethod
    def register(cls, func):
        cls._filters[func.__qualname__] = func
        return func


# == Filters
class Link:
    @Filter.register
    def as_name(val, target):
        return f"[{val}]({target})"

    @Filter.register
    def as_target(val, name):
        return f"[{name}]({val})"


@Filter.register
def get_mul(val, target):
    return [
        d[target if isinstance(d, dict) else int(target)]
        for d in val if target in d
    ]


@Filter.register
def get(val, target):
    return val[target if isinstance(val, dict) else int(target)]


@Filter.register
def ul(vals):
    return "\n".join(f"* {val}" for val in vals)


@Filter.register
def ol(vals):
    return "\n".join(f"{i+1}. {val}" for i, val in enumerate(vals))


@Filter.register
def bold(val):
    return f"__{val}__"


@Filter.register
def italic(val):
    return f"*{val}*"


@Filter.register
def strikethrough(val):
    return f"~~{val}~~"


@Filter.register
def heading(val, level=1):
    return ("#" * int(level)) + f" {val}"


@Filter.register
def tabularize(vals, *headings):
    if len(vals) == 0:
        return ""

    def row(coll, fill=" "):
        return "|" + "|".join(fill + str(val) + fill for val in coll) + "|\n"

    def generate_headings(v):
        return set(key for item in v for key in item)

    if isinstance(vals, dict) and isinstance(list(vals.values())[0], dict):
        vals = sorted(
            [dict(_=key, **vals[key]) for key in vals],
            key=lambda x: x["_"]
        )
        headings = (
            ["_"] +
            list(
                headings or
                (generate_headings(vals) - set(["_"]))
            )
        )
    elif len(headings) == 0:
        headings = generate_headings(vals)
    table = (
        row(headings) +
        row(("-" * len(heading) for heading in headings), fill="-")
    )
    for entry in vals:
        new_row = row(
            str(entry[heading]).strip().replace("\n", " ") if heading in entry else "-"
            for heading in headings
        )
        table += new_row
    return table


@Filter.register
def date(val, output_format="%x %X"):
    return datetime_parser.parse(val).strftime(output_format)


@Filter.register
def frmt(val, output_format):
    return f"{{:{output_format}}}".format(val)


@Filter.register
def adjust(val, adjustment, precision=0):
    if adjustment == "+":
        return math.ceil(float(val))
    elif adjustment == "-":
        return math.floor(float(val))
    elif adjustment == "~":
        return round(float(val), int(precision))
    else:
        raise SyntaxError(f"unkown adjustment \"{adjustment}\"")


@Filter.register
def for_each(vals, *filter_strings):
    ress = []
    for val in vals:
        if len(val) > 0:
            res = Filter.apply_filters(val, filter_strings)
            if len(res) > 0:
                ress.append(res)
    return ress


@Filter.register
def join(vals, delim, escape=None):
    if escape and delim in Filter.escape_sequences:
        delim = Filter.escape_sequences[delim]
    return delim.join(vals)


# == Templating Engine
def _compute_tag(data, match, location, verbose, default):
    if verbose:
        print(
            f"Found tag at {str(location): >10}:"
            f" {match[2:-2]}"
        )
    match_parts = match[2:-2].split("|")
    try:
        res = Filter.apply_filters(
            data[match_parts[0]],
            match_parts[1:] if len(match_parts) > 1 else None
        )
    except SyntaxError as e:
        print(
            f"<!> Found {e.args[0]} at {str(location)}.",
            f"--> \"{match[2:-2]}\"",
            sep="\n"
        )
        res = None
    except MissingKeyError as e:
        if default:
            res = default
        else:
            print(
                "<!> unkown key",
                f"--> {e.args[0]}",
                sep="\n"
            )
            res = match
    return (match, res)


def _worker(in_q, out_q, data, verbose, default):
    while True:
        work_load = in_q.get()
        if work_load is None:
            break
        else:
            match, location = work_load
            result = _compute_tag(
                data,
                match,
                location,
                verbose,
                default
            )
            out_q.put(result)
    out_q.put(None)


def fill_template(
    template_text,
    data,
    *,
    verbose=False,
    number_of_workers=1,
    default=None
):
    total_tasks = 0
    in_q = mp.Queue()
    out_q = mp.Queue()

    for match in re.compile(r"{{[^\}]*}}").finditer(template_text):
        in_q.put((match.group(0), match.span()))
        if total_tasks < number_of_workers:
            mp.Process(
                target=_worker,
                args=(in_q, out_q, data, verbose, default)
            ).start()
            total_tasks += 1

    for _ in range(total_tasks):
        in_q.put(None)

    while total_tasks > 0:
        result = out_q.get()
        if result is None:
            total_tasks -= 1
        else:
            template_text = template_text.replace(*result)

    return template_text


# == CLI
if __name__ == "__main__":
    import argparse
    import os
    from collections import namedtuple

    Target = namedtuple("Target", ["file", "extension"])

    def get_file(accessor):
        def inner(path):
            f = open(path, accessor)
            name, extension = os.path.splitext(path)
            return Target(f, extension[1:])

        return inner

    def positive_int(val):
        try:
            i = int(val)
            if i <= 0:
                raise argparse.ArgumentTypeError(f"{i} <= 0")
        except Exception as e:
            raise argparse.ArgumentTypeError(e.args(0))

    parser = argparse.ArgumentParser(
        description="Fill a markdown tempalte with json data."
    )
    parser.add_argument(
        "data_file",
        metavar="D",
        type=get_file("r"),
        help="the data file to source from",
    )
    parser.add_argument(
        "template_file",
        metavar="T",
        type=argparse.FileType("r"),
        help="the template to fill",
    )
    parser.add_argument(
        "output_file",
        metavar="O",
        type=argparse.FileType("w"),
        help="the file to save the result in",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="display processing state"
    )
    parser.add_argument(
        "-t",
        "--type",
        type=str,
        default='default',
        choices=['default'] + list(DataContainer._available_containers.keys()),
        help="read data file as certain type"
    )
    parser.add_argument(
        "-n",
        "--number_of_workers",
        type=positive_int,
        default=1,
        help="determin the number of concurrent workers"
    )
    parser.add_argument(
        "-d",
        "--missing_key_default",
        type=str,
        default=None,
        help="default value for a missing key"
    )
    args = parser.parse_args()
    try:
        mp.set_start_method('spawn')
        data = DataContainer.make_container(
            args.type if args.type != 'default' else args.data_file.extension,
            args.data_file.file
        )
        template_text = args.template_file.read()
        new_text = fill_template(
            template_text,
            data,
            verbose=args.verbose,
            number_of_workers=args.number_of_workers,
            default=args.missing_key_default
        )
        args.output_file.seek(0)
        args.output_file.write(new_text)
    except Exception as e:
        raise e
    finally:
        args.data_file.file.close()
        args.template_file.close()
        args.output_file.close()
