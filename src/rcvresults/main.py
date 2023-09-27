"""
Script to generate HTML snippets for an election's RCV contests.

Usage:

  $ python src/rcvresults/main.py --help

For example:

  $ python src/rcvresults/main.py config/election-2022-11-08.yml \
      translations.yml data/input-reports/2022-11-08 --report-format excel \
      --output-dir final
"""

import argparse
import logging
from pathlib import Path

import rcvresults.election as election_mod
import rcvresults.parsing as parsing
import rcvresults.utils as utils


_log = logging.getLogger(__name__)

DEFAULT_REPORT_FORMAT = 'xml'

DESCRIPTION = """\
Generate HTML result snippets for an election's RCV contests.
"""


# TODO: add an option to suppress intermediate json file creation?
def make_arg_parser():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        'config_path', metavar='CONFIG_PATH', help=(
            'path to the election.yml file configuring results reporting '
            'for the election.'
        )
    )
    parser.add_argument(
        'translations_path', metavar='TRANSLATIONS_PATH', help=(
            'path to the translations.yml file to use.'
        )
    )
    parser.add_argument(
        'reports_dir', metavar='REPORTS_DIR', help=(
            'directory containing the input XML or Excel RCV reports.'
        )
    )
    parser.add_argument(
        '--report-format', default=DEFAULT_REPORT_FORMAT,
        choices=('excel', 'xml'), help=(
            'what report format to read and parse (can be "xml" for .xml '
            f'or "excel" for .xlsx). Defaults to: {DEFAULT_REPORT_FORMAT}.'
        )
    )
    parser.add_argument(
        '--output-dir', default='output', help=(
            'the directory to which to write the output files.'
        )
    )
    return parser


def get_xml_paths(dir_path):
    return utils.get_paths(dir_path, suffix='xml')


def get_excel_paths(dir_path):
    original_paths = utils.get_paths(dir_path, suffix='xlsx')
    paths = []  # the return value
    for path in original_paths:
        file_name = path.name
        if file_name.startswith('~'):
            _log.warning(f'skipping temp file: {path}')
            continue
        paths.append(path)

    return paths


def get_report_paths(reports_dir, extension):
    _log.info(f'gathering {extension} reports in: {reports_dir}')

    if extension == 'xlsx':
        paths = get_excel_paths(reports_dir)
    else:
        assert extension == 'xml'
        paths = get_xml_paths(reports_dir)

    return paths


# TODO: move / rename this module to scripts/make_reports.py, and change
#  it to accept a list of json paths.
def main():
    log_format = '[{levelname}] {name}: {message}'
    logging.basicConfig(format=log_format, style='{', level=logging.INFO)

    parser = make_arg_parser()
    args = parser.parse_args()

    config_path = Path(args.config_path)
    translations_path = Path(args.translations_path)
    reports_dir = Path(args.reports_dir)
    output_dir = Path(args.output_dir)

    if args.report_format == 'xml':
        report_suffix = 'xml'
    else:
        assert args.report_format == 'excel'
        report_suffix = 'xlsx'

    report_paths = get_report_paths(reports_dir, extension=report_suffix)

    json_dir = output_dir / 'json'
    json_paths = parsing.make_jsons(report_paths, output_dir=json_dir)

    # TODO: pass css_dir.
    election_mod.process_election(
        json_paths, config_path=config_path,
        translations_path=translations_path, output_dir=output_dir,
    )


if __name__ == '__main__':
    main()
