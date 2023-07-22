# Dominion RCV Results Reporter

A Python script to generate HTML snippets of the round-by-round results
of ranked choice voting (RCV) contests from the results reports generated
by Dominion's Democracy Suite.

The script parses both the XML and Excel (`.xlsx`) reports output by
the Dominion system.

## Overview

This project enables the round-by-round results of RCV contests to be
displayed as part of an HTML election results summary page for several
contests.

For example, using San Francisco's November 2022 election as an example,
the RCV contest for the District Attorney might look like this.

![Screenshot of an HTML summary of the November 2022 District Attorney
RCV contest, as generated by this
project](docs/images/2022-11-DA-Summary.png)

Notice in the example above that both the first and final rounds are shown,
and the leading candidate is highlighted in green.
The final round is the most important round because it shows which
candidate is leading.

## Advantages

Some advantages:

* HTML is more accessible than the system's default PDF reports.
* The HTML generated by this project can be made to support multiple
  languages and customized in other ways to increase accessibility and
  readability.
* Using HTML snippets allows the results of multiple RCV contests to be
  viewed on a single page. This way members of the public don't need to
  click to a different page for each RCV contest.
* The tables in Dominion's PDF reports are also inconveniently split
  by page breaks, which makes them harder to read, as can be seen below.
  ![Screenshot of Dominion PDF page
  break](docs/images/2022-11-DA-Dominion-PDF.png)

## Requirements

This project is intended for use with Dominion's Democracy Suite 5.10A.
This is the Dominion voting system that the [California Secretary of State
approved](https://www.sos.ca.gov/elections/ovsta/frequently-requested-information/dominion-voting)
in July 2020 (with approvals of subsequent modifications in 2021 and later).

## Usage

TODO

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

## TODO

* Support parsing XML.
* Make test HTML viewable on GitHub.
* Add end-to-end tests of the html.
* Add intermediate rounds? (expand / collapse)
