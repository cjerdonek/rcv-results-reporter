# RCV Results Reporter for use with Dominion Voting

An open-source Python script to generate HTML snippets of the
round-by-round results of ranked choice voting (RCV) contests from
the results reports generated by Dominion's Democracy Suite.

The script can parse either the XML or Excel (`.xlsx`) RCV reports
generated by the Dominion system. However, XML is the preferred report
to parse since it's more structured and is an open data format.

## Overview

This project enables the round-by-round results of Dominion RCV contests
to be displayed in an HTML format in multiple languages, in addition to
Dominion's default English-only formats of PDF, Excel, and XML.

The HTML results can also be rendered in an abbreviated form for
inclusion in an HTML election results summary page of several contests.
The following screenshot shows one possibility for how an RCV contest
could be displayed in a summary form. This example is for the District
Attorney contest in San Francisco's November 2022 election:

![Screenshot of an HTML summary of the November 2022 District Attorney
RCV contest, as generated by this
project](docs/images/2022-11-DA-Summary.png)

Notice in the example above that both the first and final rounds are shown,
and the leading candidate (and their final-round vote total) is
highlighted in green.
The final round is the most important round to show because it shows which
candidate is leading.

## Advantages

Some advantages of using this project:

* HTML is more accessible than Dominion's PDF reports for people with
  vision impairment or low vision. For example, screen reader software
  works better with HTML.
* The HTML generated by this project can be made to support multiple
  languages, whereas the default reports are English-only.
* The HTML can also be customized in other ways to increase accessibility,
  readability, and convenience. For example, things like additional
  highlighting or styling, sorting of rows, and links to additional
  explanatory material can all be added.
* Using HTML snippets lets the results of multiple RCV contests be
  viewed on a single page. This way members of the public don't need to
  click to a different page for each contest to see who the winner is
  and what the final-round vote totals are.
* The tables in Dominion's PDF reports can also be inconveniently split
  by page breaks, which makes them harder to read. For example, this can
  be seen in the screenshot below of a PDF report from the November 2022
  election:
  ![Screenshot of Dominion PDF page
  break](docs/images/2022-11-DA-Dominion-PDF.png)

## Demo

To see a demo page, you can go
[here](https://cjerdonek.com/rcv-results-reporter/).
The demo shows RCV summary tables for the November 2019, November 2020,
February 2022, and November 2022 elections.

TODO: mention this page: https://civicdesign.org/topics/rcv/

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
   the contest (e.g. one for each language).
   These snippets are then saved to individual files. These HTML snippets
   can then be included in a larger HTML summary page, like they are in
   the sample demo page.

   To generate the HTML snippets, the code uses a single
   [Jinja](https://jinja.palletsprojects.com/) template located
   [here](templates/rcv-summary.html), and a YAML file located
   [here](translations.yml) of translations of words used in the
   Dominion's original reports (words like "Overvotes," "Exhausted," and
   "Continuing Ballots"). The template can be customized as needed to
   control exactly how the HTML snippets look, and the YAML file can be
   expanded to support more languages and cover more words.
   [Here](data/output-html/rcv-snippets/2022-11-08/da_short-en.html) is
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

Install Python. Any recent version should work, e.g. Python 3.8 or newer.

Install Python requirements and the project itself (preferably within
a Python virtual environment):

```
$ pip install -r requirements/requirements.txt
$ pip install -e .
```

## Usage

To run the demo:

```
$ python src/rcvresults/main.py
```

TODO: add a script that can be used in a more general, non-demo context.

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

BSD 3-Clause License, Copyright (c) 2023, Chris Jerdonek

## TODO

* Add translations of the following phrases used in Dominion's English
  RCV reports:
  * Continuing Ballots Total
  * Blanks
  * Exhausted
  * Non Transferable Total
* Make test HTML viewable on GitHub.
* Add a "production" script for use in a non-demo context.
* Try adding intermediate rounds? (expand / collapse)
* Add end-to-end tests of the html.
* Make sure all elections are covered in the tests.
