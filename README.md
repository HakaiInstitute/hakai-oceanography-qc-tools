# Hakai Oceanography Data QC tools

<!-- NOTE: All sections are placeholders. Use the relevant ones-->

![Logo](hakai_qc_app/assets/logo.png)

<!-- Make a favicon/logo using something like:

* https://favicon.io/
* https://www.shopify.com/tools/logo-maker/open-source-software
* https://primitive.lol/ -->
<!-- You can get project relevant badges from: [shields.io](https://shields.io/) -->

[![Deploy main to hakai.app](https://github.com/HakaiInstitute/hakai-oceanography-qc-tools/actions/workflows/deploy-main.yaml/badge.svg?branch=main)](https://github.com/HakaiInstitute/hakai-oceanography-qc-tools/actions/workflows/deploy-main.yaml)
[![Deploy development to hak4i.org](https://github.com/HakaiInstitute/hakai-oceanography-qc-tools/actions/workflows/deploy-development.yaml/badge.svg?branch=development)](https://github.com/HakaiInstitute/hakai-oceanography-qc-tools/actions/workflows/deploy-development.yaml)

# Hakai Data QC tools


The Hakai QC tool is a web interface used to review and QC Hakai CTD and Nutrient data. Here's an [example](https://quality-control-data.server.hakai.app/ctd/dissolved_oxygen_ml_l/contour_profiles?station=QU39&start_dt>2020-01-01&start_dt<2023-01-01) that show the data oxygen data from QU39 from Jan 2020 to Jan 2023.


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
## Run Notbooks Locally
install dependencies

```shell
  uv sync
```
Start jupyter lab

Run jupyter notebooks
```shell
  uv run --with jupyter jupyter notebook
```

Or start jupyter lab

```shell
uv run --with jupyter jupyter lab
```

navigate to the notbooks folder and open the notebook you want to run.

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
    uv sync
```

Start the development server

```shell
  uv run hakai_qc_app/app.py
```

Navigate to `http://127.0.0.1:8050/`

## Tests

To run tests, run the following command (no test available yet)

```shell
  python pytest
```

---

## Deploying

The production branch is deployed at: 
https://quality-control-data.server.hakai.app

---
The testing branch is deployed at: 
https://quality-control-data.server.hak4i.org


---

Any pushes to the development and main branches are automatically reflected on the respectives deployments.

---

## How many CTD stations still needs to be QCed

You can run the following sql script on the hakai database:

```sql
select *
from (
select
	organization,
	work_area,
	station,
	COUNT(qc.conductivity_flag) as conductivity_qced,
	count(qc.temperature_flag) as temperature_qced,
	count(qc.salinity_flag) as salinity_qced,
	count(qc.dissolved_oxygen_ml_l_flag) as dissolved_oxygen_ml_l_qced,
	count(qc.flc_flag) as flc_qced,
	count(qc.par_flag ) as par_qced,
	count(cfc.hakai_id) as total_drops_available,
	sum(case when qc.temperature_flag is null then 1 else 0 end) as temperature_unqced,
	max(case when qc.temperature_flag notnull then cfc.start_dt else null end) as most_recent_temperature_qced_drop_start_dt
from
	ctd.ctd_qc qc
right join ctd.ctd_file_cast cfc on
	qc.ctd_cast_pk = cfc.ctd_cast_pk
where cfc.organization ='HAKAI'
and (status is null or status = '')
and cfc.processing_stage > '1_datCnv'
group by
	(cfc.organization,
	cfc.work_area ,
	cfc.station)
order by organization, work_area , station
) as subset
where total_drops_available > 2
;
```

This will give you something like [this](unqced_data_2024-08-29.csv)

Or go see here: <https://hakai-ctd-qc.server.hakai.app/manual-qc-status>
