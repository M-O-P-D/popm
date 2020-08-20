# popm: Public Order Policing Model

[![License](https://img.shields.io/github/license/mashape/apistatus.svg)](https://opensource.org/licenses/MIT)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/220e164b605d4dd98771a5ab7e9281d1)](https://www.codacy.com?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=M-O-P-D/popm&amp;utm_campaign=Badge_Grade)
![status](https://img.shields.io/badge/dev%20status-work%20in%20progress-red)

![screenshot](./doc/screenshot.png)

## Status

- [X] Initialise available PSUs in each area according to available resources and limits
- [X] Allocate PSUs within event's force area
- [ ] Allocate PSUs as necessary from other force areas within alliance
- [ ] Allocate PSUs if necessary from force areas outside alliance
- [ ] Move PSUs to events

## Developer Setup

`popm` is written in python3 and uses the [mesa](https://mesa.readthedocs.io/en/master/) ABM framework with the [mesa-geo](https://github.com/Corvince/mesa-geo) mapping extension. Use of a virtualenv or similar is recommended, but not essential. A [Dockerfile](./Dockerfile) is provided for containerisation and deployment.

### Native

Firstly, install dependencies

```bash
pip install -r requirements.txt
```

Then, run the server:

```bash
mesa runserver .
```

### Docker

e.g.

```bash
docker build -t MOPD/popm .
```

to run on default http port:

```bash
docker run --rm -d -p 80:8521/tcp virgesmith/popm:latest
```

to push to the M.O.P.D. repository:

```bash
docker push mopd/popm:latest
```

### Troubleshooting

If the dependencies don't install, giving errors like `undefined symbol: Error_GetLastErrorNum` it may be because `mesa-geo` package has an external (non-python) dependency on (e.g.) `libspatialindex-dev` which can be installed with e.g. apt.

## Deployment

TODO...

## Data Sources

- Boundary data: [http://geoportal.statistics.gov.uk](http://geoportal.statistics.gov.uk/datasets/police-force-areas-december-2016-ultra-generalised-clipped-boundaries-in-england-and-wales-1?geometry=-22.401%2C48.023%2C18.117%2C57.305)
- Population data (6/2019 is the latest complete dataset): [https://www.ons.gov.uk/peoplepopulationandcommunity/crimeandjustice/datasets/policeforceareadatatables](https://www.ons.gov.uk/peoplepopulationandcommunity/crimeandjustice/datasets/policeforceareadatatables)
