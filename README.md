# RCV Results Reporter for use with Dominion's Voting System

[![cjerdonek](https://circleci.com/gh/cjerdonek/rcv-results-reporter.svg?style=svg)](https://circleci.com/gh/cjerdonek/rcv-results-reporter)

This project contains an open-source Python script to generate HTML
snippets of the round-by-round results of ranked choice voting (RCV)
contests from the RCV results reports generated by Dominion's
Democracy Suite voting system.

The script can parse both the XML and Excel (`.xlsx`) RCV reports
from Dominion's system. (XML is the preferred report to parse
since it's more structured and is an open data format.)

For a demo page showing examples generated for all RCV contests
in the elections from 2019 to 2022, go here:

* https://cjerdonek.github.io/rcv-results-reporter

Also see a [memo](https://sf.gov/sites/default/files/2023-09/Multilanguage_Open_Source_RCV_Results_Reporter.pdf)
about this project that was included in the agenda packet of the
San Francisco Elections Commission's
[September 20, 2023 Regular Meeting](https://sf.gov/meeting/september-20-2023/elections-commission-regular-meeting) under agenda item #5.

## Overview

This project enables the round-by-round results of Dominion RCV contests
to be displayed in an accessible, HTML format in multiple languages,
in addition to Dominion's default, English-only formats of PDF, Excel,
and XML.

For example, below is a screenshot taken from the demo above of the
round-by-round page this project produces for San Francisco's November
2022 District Attorney contest.

![Screenshot of an HTML page of the round-by-round results of the
November 2022 District Attorney RCV contest, as generated by this
project](docs/images/2022-11-DA-Rounds.png)

(The HTML format above is an improved version of the English-only HTML
format that Dominion's voting system used to generate before 2019 but
doesn't anymore. See
[here](https://www.sfelections.org/results/20181106/data/20181127/d2/20181127_d2.html)
for an example of that from a 2018 contest.)

This project can also output RCV results in a short summary format
for inclusion in a results summary page of several contests.
For example, below is another screenshot from the demo of the summary
this project made for the same contest as above.

![Screenshot of an HTML summary of the November 2022 District Attorney
RCV contest, as generated by this
project](docs/images/2022-11-DA-Summary.png)

The format of the summary table above is closely modeled after the
[Center for Civic Design's](https://civicdesign.org/) May 2023
[best practice recommendations](https://civicdesign.org/topics/rcv/)
for summary displays. (See the "Results Displays in News Articles" PDF
on the linked page, which the document emphasizes is also relevant
to election office results displays).

Notice how the summary shows both the first and last rounds, and
the leading candidate (and their final-round vote total) is highlighted
in green. The final round is the most important round to show because
it shows which candidate is leading.

## Advantages

Some advantages of using this project:

* HTML is much more accessible than Dominion's PDF reports for people
  with vision impairment or low vision. For example, screen reader
  software works better with HTML.
* The HTML generated by this project can be made to support multiple
  languages, whereas the default reports are English-only.
* The HTML can also be customized in other ways to increase accessibility,
  readability, and convenience. For example, things like additional
  highlighting or styling, sorting of rows, and links to additional
  explanatory material can all be added (like definitions of terms
  like "continuing ballots" and "exhausted ballots").
* Using HTML snippets lets the results of multiple RCV contests be
  viewed on a single page. This way members of the public don't need to
  click to a different page for each contest to see who the winner is
  and what the final-round vote totals are.
* The tables in Dominion's existing PDF reports can be inconveniently
  split by page breaks, which makes them harder to read. This can be
  seen, for example, in the screenshot below of a PDF report from the
  November 2022 election:
  ![Screenshot of Dominion PDF page
  break](docs/images/2022-11-DA-Dominion-PDF.png)
* Using the script in this project doesn't require any changes to how
  Dominion's voting system is used or configured. It can use the RCV
  results reports already generated by the system.

## Demo

To see a demo page, you can go
[here](https://cjerdonek.github.io/rcv-results-reporter/).
The demo shows RCV summary tables for the November 2019, November 2020,
February 2022, and November 2022 elections.

## How it Works

The code works like this:

1. First, the code reads in an XML or Excel report for an RCV contest
   from the Dominion system and extracts the candidate names and
   vote subtotals for each round. Optionally, this intermediate
   information can be saved to a JSON file before proceeding to the
   next step. [Here](data/output-json/2022-11-08/da_short.json)
   is an example of what such a JSON file looks like (for the same
   contest from the screenshots above).
2. Second, the code takes the candidate names and vote subtotals
   from the previous step and generates one or more HTML snippets for
   the contest (e.g. one for each template and language).
   These snippets are then saved to individual files. These HTML snippets
   can then be included in a larger HTML summary page, like they are in
   the sample demo page.

   To generate the HTML snippets, the code uses two
   [Jinja](https://jinja.palletsprojects.com/) templates located
   [in this directory](templates), and a YAML file located
   [here](translations.yml) of translations of words used in the
   Dominion's original reports (words like "Overvotes," "Exhausted," and
   "Continuing Ballots"). The templates can be customized as needed to
   control exactly how the HTML snippets look, and the YAML file can be
   expanded to support more languages and cover more words.
   [Here](data/output-html/rcv-snippets/2022-11-08/summary-tables/da_short-summary-en.html) is
   an example of what such an HTML snippet might look like
   (again for the same contest as above), and
   [here](data/output-html/rcv-snippets/2022-11-08) is the directory
   of all HTML snippets used in the demo for the November 2022 election.

All of the above takes less than a second to run.

## Requirements

This project is intended for use with Dominion's Democracy Suite 5.10A.
This is the Dominion voting system that the [California Secretary of State
approved](https://www.sos.ca.gov/elections/ovsta/frequently-requested-information/dominion-voting)
in July 2020 (with approvals of subsequent modifications in 2021 and later).

## Setup

Install Python. The project is tested with the following versions of Python:

* Python 3.9
* Python 3.10
* Python 3.11

(See [here](https://devguide.python.org/versions/) for which Python versions
are still current.)

Install Python requirements and the project itself (preferably within
a Python virtual environment):

```
$ pip install -r requirements/requirements.txt
$ pip install -e .
```

## Usage

To run the demo (includes four elections):

```
$ python src/rcvresults/scripts/build_demo.py
```

To generate HTML snippets for a single election:

```
$ python src/rcvresults/main.py --help
usage: main.py [-h] [--report-format {excel,xml}] [--output-dir OUTPUT_DIR]
               CONFIG_PATH TRANSLATIONS_PATH REPORTS_DIR

Generate HTML result snippets for an election's RCV contests.

positional arguments:
  CONFIG_PATH           path to the election.yml file configuring results
                        reporting for the election.
  TRANSLATIONS_PATH     path to the translations.yml file to use.
  REPORTS_DIR           directory containing the input XML or Excel RCV
                        reports.

optional arguments:
  -h, --help            show this help message and exit
  --report-format {excel,xml}
                        what report format to read and parse (can be "xml"
                        for .xml or "excel" for .xlsx). Defaults to: xml.
  --output-dir OUTPUT_DIR
                        the directory to which to write the output files.
```

For example (this should work from the repo root):

```
  $ python src/rcvresults/main.py config/election-2022-11-08.yml \
      translations.yml data/input-reports/2022-11-08 --report-format excel \
      --output-dir final
```

## Developing

To run tests:

```
$ python -m unittest discover rcvresults
```

"Tidied" versions of the HTML files in the `html` directory were generated
using HTML [Tidy](https://www.html-tidy.org/).

For example:

```
$ tidy -output html/2020-11-03/index-tidied.html -utf8 html/2020-11-03/index-original.html
```

## License

BSD 3-Clause License

Copyright (c) 2023, Chris Jerdonek
