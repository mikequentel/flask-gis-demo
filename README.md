# Flask GIS Demo https://github.com/mikequentel/flask-gis-demo

* A reference implementation of a REST-exposed GIS server using Flask. Includes use of PostgreSQL database. It is a proof-of-concept and a demo of how one can implement a REST GIS server. It is not meant to be a robust, production-quality solution, but rather an example and potential starting point for future projects.
* Database: [PostgreSQL](https://www.postgresql.org)
  * Based on restaurant inspection data, from several years ago (circa 2013), collected by the state of New York and shared at the USA government website [data.gov](https://www.data.gov)
    * This is publicly available information published by the US government.
  * The backend database for this demo does not include PostGIS at this time.
  * Contains a flat table named `restaurants`--not a normalised database, for simplicity of the demo.
* Connection to database: [psycopg2](http://initd.org/psycopg)
* Circle distance calculation uses the libraries [geographiclib](https://pypi.python.org/pypi/geographiclib) and [geopy](https://pypi.python.org/pypi/geopy)

# Interfaces
## Note about the REST interfaces
* At this time, the interfaces are GET (read-only) actions.

## Examples of included interfaces--one exists for each field in the database.
* Select top (limit) of items **/restaurants/limit/{limit}**
* Select by object ID **/restaurants/oid/{oid}**
* Select by circle (items within the circle), with parameters latitude, longitude, and radius in km **/restaurants/circle/{circle}**
* Select by bounding box (items within bounding box), with parameters upper left latitude, upper left longitude, lower right latitude, lower right longitude **/restaurants/bbox/43.000000,-79.000000,41.000000,-71.000000**
* Select by facility (restaurant) name **/restaurants/facility/{facility}**
* Select by county containing facilities of interest **/restaurants/county/{county}**

# Hacking

## Prerequisites
* PostgreSQL
* Python (version 2.7 was used for the demo but you could use 3 instead)
* Pip
* Virtualenv
* Flask

## Steps
1. Clone the Git repository: `git clone https://github.com/mikequentel/flask-gis-demo.git`
2. Enable the Virtual Environment (via `virtualenv`) and then load the pre-requisite libraries: `pip install -r requirements.txt`
3. Install a local copy of the database `businesses` which contains the table `restaurants` by using the plain text dump `data/businesses_backup.sql`--example: assuming database named `businesses` already exists (that is, you already created the database), then for user `postgres`, run the command: `psql -U postgres -h localhost --set ON_ERROR_STOP=on businesses < businesses_backup.sql`
4. Set the appropriate credentials, which set environment variables used to connect to the database.
5. Start the server locally by running `export FLASK_APP=app.py; flask run` which will deploy the server to http://localhost:5000
6. Now, you can run queries against the server through any HTTP client, but most easily through using the example at `client/map.html`

## Running via Docker
1. Install and configure the database `businesses` which has the table `restaurants`, as mentioned in the Hacking steps, and run the PostgreSQL service.
2. Run the script `rundocker.sh`, which has commands for running the demo in a Docker container, serving over port `8888`, so you can access it at http://localhost:8888
