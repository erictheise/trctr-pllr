# TRCTR-PLLR

_TRCTR-PLLR_ is a _faker_ for United States location data. It's useful when you need point data that is representative of where people live as reported by the Census Bureau.


## How it works

For each requested observation, _TRCTR_PLLR_ randomly selects a Census Tract using population-based weights. It then generates a location based on the bounding box of the Tract and tests to see if that point is contained by the Tract's actual boundaries. If not, it will generate and test up to 999 more locations. In the atypical case that none of the 1,000 generated points are contained in that Tract, it will randomly select a different Tract. This does introduce a bias that would be dubious in a tool that required statistical validity, but this is merely a _faker_.

_TRCTR-PLLR_ uses population data from the 2010 Census and Tract boundary data from 2017.

_TRCTR-PLLR_ returns the Tract's `geoip`, `usps`, and `pop10` from the original Census data and allows you to specify one additional property. I developed _TRCTR_PLLR_ to prototype maps and used values of the additional property to set the fill color: how does a 3 color, 6 color, 12 color map render with 100 points, 1000 points, 10,000 points?


## Prerequisites

I assume you have basic familiarity with the command line, with GitHub, and have a preferred package manager for your platform (e.g. [homebrew](https://brew.sh) for OS X). You'll need [PostgreSQL](https://www.postgresql.org/) with [PostGIS extensions](http://postgis.org/), but if you're doing geo work, you almost certainly already have these. You'll need Python 3 and you'll want a virtual environment manager such as [virtualenv](https://virtualenv.pypa.io/en/stable/) or [venv](https://docs.python.org/3/library/venv.html). Everything else is installed via `pip`.


## Installation

* `git clone` this repository or install a [release](https://github.com/erictheise/trctr-pllr/releases).
* create a virtual environment.
* install the required libraries.

  `pip install -r requirements.txt`

* create a database.

  `CREATE DATABASE `

* load the data.

* start the application.

```
FLASK_APP=trctr_pllr.py flask run
```

## Hosted version

A [hosted version of the application](https://trctr-pllr.herokuapp.com/) is presently available at heroku but may be taken down at any time.

## Usage

### Web interface

* select the number of observations you need.
* select the format of the output you need.
* if you'd like to generate an additional random property, e.g., color, click the __Yes, please__ button. Name the property, specify the number of variants, then specify the values and weights of their occurrence. Weights are neither probabilities nor percents and do not need to sum to 1 or 100%.
* click the __Generate features__ button.
* if you like the looks of the generated data, copy and paste the contents of the __Output__ window into your own file.

![Web interface example](https://github.com/erictheise/trctr-pllr/blob/master/images/web-interface-example.png)

### API

The web interface prepares a call to the application's simple API. You can `GET` from it directly at `/tracts`. The parameters are:

* `observations`: required. Integer.
* `geoid`: optional. `on` to include Census Bureau Tract identifier in output.
* `usps`: optional. `on` to include two letter state or territory identifier in output.
* `pop10`: optional. `on` to include Census Bureau Tract population in output.
* `format`: required. One of `geojson`, `csv`, `tsv`.
* 
