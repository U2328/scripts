# md_toc
A simple way to add a table of contents to a pure markdown file.

```
usage: mdtoc.py [-h] [-l] [-v] [-d D] [-m M] [-H H] [-o O] S

Inject ToC into md-file

positional arguments:
  S                  the file to source from

optional arguments:
  -h, --help         show this help message and exit
  -l, --linked       make ToC entries linked
  -v, --verbose      show current processing state
  -d D, --depth D    make ToC entries linked
  -m M, --marker M   the location to add the ToC
  -H H, --heading H  header of the ToC
  -o O, --output O   the location to add the ToC
```
*made on 2018-07-16 by Tim Fischer*

# ipynb_converter
A simple way to convert an iPython notebook into some different formats, without having to start the kernel.

```
usage: ipynb_converter.py [-h] [-f F] [-F] S T

Convert an iPython notebook into different formats.

positional arguments:
  S                 the file to source from
  T                 the file to write to

optional arguments:
  -h, --help        show this help message and exit
  -f F, --format F  format to convert to
  -F, --force       forcefully open file
```
*made on 2018-07-18 by Tim Fischer*

# md_template
A small tool to fill a "*md template*" from json data.

```
usage: md_template.py [-h] [-v] [-t {default,json}] [-n NUMBER_OF_WORKERS]
                      [-d MISSING_KEY_DEFAULT]
                      D T O

Fill a markdown tempalte with json data.

positional arguments:
  D                     the data file to source from
  T                     the template to fill
  O                     the file to save the result in

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         display processing state
  -t {default,json}, --type {default,json}
                        read data file as certain type
  -n NUMBER_OF_WORKERS, --number_of_workers NUMBER_OF_WORKERS
                        determin the number of concurrent workers
  -d MISSING_KEY_DEFAULT, --missing_key_default MISSING_KEY_DEFAULT
                        default value for a missing key
```
*made on 2018-07-22 by Tim Fischer*
*last worked on 2018-08-20 by Tim Fischer*

# weather
Very tiny "*cli*" for fetching weather data via wttr.in

```
usage: weather.py [-h] [-d] L

Fetch weather data via wttr.in

positional arguments:
  L             the target location

optional arguments:
  -h, --help    show this help message and exit
  -d, --detail  the level of detail
```
*made on 2018-08-15 by Tim Fischer*
