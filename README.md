# Resonanz Development Assessment


## Getting started

### Configuration

The application can be configured in several ways - through config (or through environment variables for the DB).
The config file can be specified with the `--config [filename]` and if it's missing, the application looks for `config.json` in the project root.
The docker deployment looks for `docker_config.json` in the project root.

The config structures will be outlined below with the possible fields and the corresponding env var, if any.

#### Config
| Config field           | Type           | Default        | Explanation                                                                                                              |
|------------------------|----------------|----------------|--------------------------------------------------------------------------------------------------------------------------|
| port                   | int            | 80             | port for the application to listen on                                                                                    |
| debug_mode             | bool           | False          | if true, use local flask server, otherwise use waitress WSGI                                                             |
| log_level              | string         | DEBUG or ERROR | log level (one of DEBUG (default if debug_mode == True), INFO, WARNING, ERROR (default if debug_mode==False)             |
| address_parser_backend | string         | googlemaps     | backend for normalizing addresses. must be one of "nominatim" or "googlemaps". If using "googlemaps, api key is required |
| address_parser_api_key | string         |                | API key for Google Maps. Only required if parser backend==googlemaps                                                     |
| database               | DatabaseConfig |                | *see structure below*                                                                                                    |


#### DatabaseConfig
| Config field | Env var equivalent | Type   | Default    | Explanation                                                               |
|--------------|--------------------|--------|------------|---------------------------------------------------------------------------|
| db_type      | DATABASE_ENGINE    | string | sqlite     | which database backend to use. application can use `sqlite` or `postgres` |
| username     | DATABASE_USER      | string | postgres   | user for database, *not needed for sqlite*                                |
| password     | DATABASE_PASSWORD  | string | NOT_SET    | password for database, *not needed for sqlite*                            |
| host         | DATABASE_HOST      | string | localhost  | network location of the database, *not needed for sqlite*                 |
| port         | DATABASE_PORT      | int    | -1         | port on which the database is listening, *not needed for sqlite*          |
| db_name      | DATABASE_NAME      | string | resonanz   | name of the database to be created and used by the app                    |

 - **Assuming database engine connection is possible, the application will create its own db and tables.**


### Local deployment

#### Requirements

 - Python 3.10+
 - poetry

#### Steps

1. Clone the repo + enter `git clone git@github.com:zkscpqm/resonanz-task.git && cd resonanz-task`
2. Install dependencies with `poetry install`
3. Ensure the config file is correctly filled in (see above or the config_template.json)
4. Run the server with `poetry run python main.py`

### Docker deployment

 - The only current docker deployment makes use of postgresql by default, so ensure the config file takes this into account.
 - Remember to have a docker_config.json for this!

#### Requirements

 - Docker + compose

#### Steps

1. Clone the repo and enter the deployment directory `git clone git@github.com:zkscpqm/resonanz-task.git && cd resonanz-task/deploy`
2. Ensure the docker config file is correctly filled in (see above or the config_template.json)
3. Run the server with `docker-compose up -d`


## Usage

The application features a web interface available at the port selected in the config (default 80)
The web interface has two pages which can be reached from the NavBar: Search and Insert/Upload

### Search `GET [/, /search]`

 - This page allows you to search by address or by tenant name. The search is case-insensitive.
 - The search will return all addresses that match the query, along with the tenants that live there.
 - If no search is entered, all addresses and tenants will be returned.
 - The results can also be downloaded as a text file


### Insert/Upload `GET /insert`

 - This page allows you to insert a single address and tenant, or upload a CSV file with multiple addresses and tenants.
 - The CSV file must have a header and 2 columns, with the first being the tenant name and the second being the address.
 - Multiple tenants can be matched to one address as long as the input address lines are  normalized to the same value (eg same address written in different languages).
 - Multiple tenants can have the same name, but they will be treated as different entities.
 - The CSV file is streamed to the backend, so it can be arbitrarily large


## REST Endpoints (only for FE/BE communication)

 - `GET /search/_addresses` -> Expects optional query param `?name={tenant_name}`, if the query param is not given, all results are returned, otherwise, return all addresses where the tenant has the name provided
 - `GET /search/_tenants` -> Expects optional query param `?address={address}`, if the query param is not given, all results are returned, otherwise, return all tenants that live at the address provided
 - `POST /insert/_tenant` -> Expects a json body with the following structure: `{"name": "tenant_name", "address": "tenant_address"}` and it attempts to insert the tenant and address into the database. If the address resolves to an existing one, the tenant is added to the existing address, unless there is already a tenant at that address with the same name
 - `POST /insert/_batch` -> Expects a csv file as described above and attempts to insert all the tenants and addresses into the database following the ruleset in /insert/_tenant

### TODO:

#### Backend

 - [x] Set up Flask
 - [x] Set up database
 - [x] Set up Logging
 - [x] Normalize addresses and choose best backend
   - [x] Get basic functionality with Nominatim
   - [x] Get basic functionality with Google Maps API
 - [x] Implement address matching
 - [x] Implement loading CSVs
 - [x] Normalize names? (use as lower for easy matching and have Capitalized for return)

#### Frontend

 - [x] Set up basic ~~HTMX~~ jQuery, bootstrap
 - [ ] ~~Set up basic map/locator~~
 - [x] Implement csv batch loading and streaming to BE
 - [x] Implement results download
 - Views:
   - [x] Home/Search
   - [x] Add address/tenant
   - ~~Some settings~~

#### Deployment

 - [x] Bare metal default (debug)
 - [x] Bare metal with WSGI
 - [x] Docker
