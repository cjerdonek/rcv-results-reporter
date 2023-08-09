"""
Script to generate HTML snippets for an election's RCV contests.

Usage:

  $ python src/rcvresults/main.py --help

"""

import argparse
import functools
import logging
from pathlib import Path

import jinja2
from jinja2 import Environment, FileSystemLoader

import rcvresults.parsers.xml as xml_parsing
import rcvresults.parsers.xslx as excel_parsing
import rcvresults.rendering as rendering
import rcvresults.summary as summary
import rcvresults.utils as utils
from rcvresults.utils import LANG_CODE_ENGLISH


_log = logging.getLogger(__name__)

DEFAULT_REPORT_FORMAT = 'xml'

DESCRIPTION = """\
Generate HTML result snippets for an election's RCV contests.
"""


# TODO: add a translations_path argument.
def make_arg_parser():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        'config_path', metavar='CONFIG_PATH', help=(
            'path to the election.yml file to configure the results '
            'reporting for the election.'
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


def load_label_translations(translations_path):
    data = utils.read_yaml(translations_path)
    labels = data['labels']
    return labels


def load_phrases(translations_path):
    data = utils.read_yaml(translations_path)
    labels = data['labels']
    phrases = {}
    for label, translations in labels.items():
        phrase = translations[LANG_CODE_ENGLISH]
        phrases[phrase] = label

    return phrases


def make_environment(translations_path):
    env = Environment(
        loader=FileSystemLoader('templates'),
        # TODO: pass the autoescape argument?
    )

    translated_labels = load_label_translations(translations_path)
    translate_label = functools.partial(
        rendering.translate_label, translated_labels=translated_labels,
    )
    phrases = load_phrases(translations_path)
    translate_phrase = functools.partial(
        rendering.translate_phrase, translated_labels=translated_labels,
        phrases=phrases,
    )

    env.filters.update({
        'format_int': rendering.format_int,
        'format_percent': rendering.format_percent,
        'TL': jinja2.pass_context(translate_label),
        'TP': jinja2.pass_context(translate_phrase),
    })
    return env


def make_html_snippets(json_path, template, output_dir):
    _log.info(f'making RCV html from: {json_path}')
    rcv_data = utils.read_json(json_path)
    base_name = json_path.stem
    rendering.make_rcv_contest_html(
        rcv_data, template=template, html_dir=output_dir,
        base_name=base_name,
    )


def process_contest(
    contest_data, reports_dir, report_suffix, template, output_dir,
):
    file_stem = contest_data['file']
    file_name = f'{file_stem}.{report_suffix}'
    report_path = reports_dir / file_name
    json_path = make_rcv_json(report_path, json_dir=output_dir)
    make_html_snippets(json_path, template=template, output_dir=output_dir)


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

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    config_data = utils.read_yaml(config_path)
    election_data = config_data['election']
    contests_data = election_data['contests']

    env = make_environment(translations_path)
    template = env.get_template('rcv-summary.html')

    for contest_data in contests_data:
        process_contest(
            contest_data, reports_dir=reports_dir, report_suffix=report_suffix,
            template=template, output_dir=output_dir,
        )


if __name__ == '__main__':
    main()
