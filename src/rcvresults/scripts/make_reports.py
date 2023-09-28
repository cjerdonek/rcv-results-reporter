"""
Script to generate HTML snippets for an election's RCV contests.

Usage:

  $ python src/rcvresults/scripts/make_reports.py --help

For example (this should work from the repo root):

  $ python src/rcvresults/scripts/make_reports.py \
      config/election-2022-11-08.yml translations.yml \
      data/output-json/2022-11-08/*.json --output-dir final

"""

import argparse
import functools
import logging
from pathlib import Path
import sys

import rcvresults.election as election_mod


_log = logging.getLogger(__name__)

DEFAULT_REPORT_FORMAT = 'xml'

DESCRIPTION = """\
Generate HTML result snippets for an election's RCV contests.
"""


class ArgumentError(Exception):

    def __init__(self, metavar, value, message):
        self.metavar = metavar
        self.message = message
        self.value = value


# This is used to create functions to pass as the "type" argument to
# ArgumentParser.add_argument().
def _file_with_suffix(path, suffix, metavar):
    path = Path(path)
    if path.suffix != suffix:
        raise ArgumentError(
            metavar, str(path), f'File path does not have suffix {suffix}',
        )
    if not path.exists():
        raise ArgumentError(
            metavar, str(path), f'File does not exist',
        )
    return path


def _make_file_type(suffix, metavar):
    """
    Return a function that can be passed as a "type" argument to
    ArgumentParser.add_argument().
    """
    return functools.partial(_file_with_suffix, suffix=suffix, metavar=metavar)


def make_arg_parser():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    # TODO: avoid having to pass the metavar twice.
    parser.add_argument(
        'config_path', metavar='CONFIG_PATH', help=(
            'path to an election.yml file configuring results reporting '
            'for the election.'
        ), type=_make_file_type('.yml', 'CONFIG_PATH'),
    )
    parser.add_argument(
        'translations_path', metavar='TRANSLATIONS_PATH', help=(
            'path to a translations.yml file to use.'
        ), type=_make_file_type('.yml', 'TRANSLATIONS_PATH'),
    )
    parser.add_argument(
        'json_paths', metavar='JSON_PATH', nargs='*', help=(
            'path to one or more json files, one per contest.'
        ), type=_make_file_type('.json', 'JSON_PATH'),
    )
    parser.add_argument(
        '--output-dir', default='output', type=Path, help=(
            'the directory to which to write the output files.'
        )
    )
    return parser


def main():
    log_format = '[{levelname}] {name}: {message}'
    logging.basicConfig(format=log_format, style='{', level=logging.INFO)

    parser = make_arg_parser()
    try:
        args = parser.parse_args()
    except ArgumentError as exc:
        file_name = Path(__file__).name
        message = (
            f'{file_name}: [ERROR] invalid {exc.metavar} argument:\n'
            f' {exc.message}: {exc.value!r}'
        )
        print(message, file=sys.stderr)
        sys.exit(1)

    config_path = args.config_path
    translations_path = args.translations_path
    json_paths = args.json_paths
    output_dir = args.output_dir

    # TODO: pass css_dir.
    election_mod.process_election(
        json_paths, config_path=config_path,
        translations_path=translations_path, output_dir=output_dir,
    )


if __name__ == '__main__':
    main()
