"""
Script to generate HTML snippets for an election's RCV contests.

Usage:

  $ python src/rcvresults/main.py --help

"""

import argparse
import logging
from pathlib import Path

import rcvresults.parsers.xml as xml_parsing
import rcvresults.parsers.xslx as excel_parsing
import rcvresults.summary as summary
import rcvresults.utils as utils


_log = logging.getLogger(__name__)

DESCRIPTION = """\
Generate HTML result snippets for an election's RCV contests.
"""


def make_arg_parser():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        'config_path', metavar='CONFIG_PATH', help=(
            'path to the election.yml file configuring the election.'
        )
    )
    parser.add_argument(
        'reports_dir', metavar='REPORTS_DIR', help=(
            'directory containing the input XML or Excel RCV reports.'
        )
    )
    parser.add_argument(
        '--report-format', default='xml', choices=('excel', 'xml'), help=(
            'what report format to read and parse. Can be "xml" (for .xml) '
            'or "excel" (for .xlsx). Defaults to: xml.'
        )
    )
    parser.add_argument(
        '--output-dir', default='output', help=(
            'the directory to which to write the output files.'
        )
    )
    return parser


def make_rcv_json(path, json_dir):
    _log.info(f'parsing: {path}')
    suffix = path.suffix
    if suffix == '.xlsx':
        parse_report_file = excel_parsing.parse_excel_file
    else:
        assert suffix == '.xml'
        parse_report_file = xml_parsing.parse_xml_file

    try:
        results = parse_report_file(path)
    except Exception:
        raise RuntimeError(f'error parsing report file: {path}')

    metadata = results['_metadata']
    contest_name = metadata['contest_name']
    candidates = results['candidates']
    _log.info(f'parsed contest: {contest_name!r} ({len(candidates)} candidates)')
    summary.add_summary(results)

    json_path = json_dir / f'{path.stem}.json'
    _log.info(f'writing: {json_path}')
    utils.write_json(results, path=json_path)

    return json_path


def process_contest(contest_data, reports_dir, report_suffix, output_dir):
    file_stem = contest_data['file']
    file_name = f'{file_stem}.{report_suffix}'
    report_path = reports_dir / file_name
    make_rcv_json(report_path, json_dir=output_dir)


def main():
    log_format = '[{levelname}] {name}: {message}'
    logging.basicConfig(format=log_format, style='{', level=logging.INFO)

    parser = make_arg_parser()
    args = parser.parse_args()

    config_path = Path(args.config_path)
    reports_dir = Path(args.reports_dir)
    output_dir = Path(args.output_dir)

    if args.report_format == 'xml':
        report_suffix = 'xml'
    else:
        assert args.report_format == 'excel'
        report_suffix = 'xlsx'

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    config_data = utils.read_yaml(config_path)
    election_data = config_data['election']
    contests_data = election_data['contests']
    for contest_data in contests_data:
        process_contest(
            contest_data, reports_dir=reports_dir, report_suffix=report_suffix,
            output_dir=output_dir,
        )


if __name__ == '__main__':
    main()
