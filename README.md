# Hakai Oceanography Data QC tools

<!-- NOTE: All sections are placeholders. Use the relevant ones-->

![Logo](src/assets/logo.png)

<!-- Make a favicon/logo using something like:

* https://favicon.io/
* https://www.shopify.com/tools/logo-maker/open-source-software
* https://primitive.lol/ -->
<!-- You can get project relevant badges from: [shields.io](https://shields.io/) -->

[![Deploy main to hakai.app](https://github.com/HakaiInstitute/hakai-oceanography-qc-tools/actions/workflows/deploy-main.yaml/badge.svg?branch=main)](https://github.com/HakaiInstitute/hakai-oceanography-qc-tools/actions/workflows/deploy-main.yaml)
[![Deploy development to hak4i.org](https://github.com/HakaiInstitute/hakai-oceanography-qc-tools/actions/workflows/deploy-development.yaml/badge.svg?branch=development)](https://github.com/HakaiInstitute/hakai-oceanography-qc-tools/actions/workflows/deploy-development.yaml)

# Hakai Data QC tools


The Hakai QC tool is a web interface used to review and QC hakai data. Here's an [example](https://quality-control-data.server.hakai.app/ctd/dissolved_oxygen_ml_l/contour_profiles?station=QU39&start_dt>2020-01-01&start_dt<2023-01-01) that show the data oxygen data from QU39 from Jan 2020 to Jan 2023.


---

## Table of Contents

<details>

<summary>Table of Contents</summary>

[Configuration](#configuration)

[Development](#development)

[Tests](#tests)

[Deploying](#deploying)

[Contributing](#contributing)

[Documentation](#documentation)

[License](#license)

</details>

---

## Configuration

To run this project locally, you will need to add the following environment variables to your `.env` file

```env
DASH_DEBUG=TRUE
LOG_LEVEL=DEBUG
DASH_HOST=127.0.0.1
ACTIVATE_SENTRY_LOG=false
```

## Development

Clone the project

```shell
  git clone git@github.com:HakaiInstitute/hakai-oceanography-qc-tools.git
```

Go to the project directory

```shell
  cd hakai-oceanography-qc-tools
```

Install dependencies

```shell
    pip install -e .
```

Start the development server

```shell
  python src/app.py
```

## Tests

To run tests, run the following command (no test available yet)

```shell
  python pytest
```

---

## Deploying

The production branch is deployed at: 
https://quality-control-data.server.hakai.app/ctd

---
The testing branch is deployed at: 
https://quality-control-data.server.hak4i.org/ctd


---

Any pushes to the development and main branches are automatically reflected on the respectives deployments.

---

## Documentation

#TODO 

---
