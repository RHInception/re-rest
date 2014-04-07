# RE-REST
Simple REST Api for our new release engine hotness.

[![Build Status](https://api.travis-ci.org/RHInception/re-rest.png)](https://travis-ci.org/RHInception/re-rest/)

## Running From Source
### With Flask
```bash
$ PYTHONPATH=src/ REREST_CONFIG=example-settings.json python src/rerest/app.py
```

### With gunicorn
```bash
$ PYTHONPATH=`pwd`/src gunicorn -e REREST_CONFIG=example-settings.json --access-logfile access.log --error-logfile=error.log rerest.app:app
```

## Unittests
Use *nosetests -v --with-cover --cover-min-percentage=80 --cover-package=rerest test/* from the main directory to execute unittests.

## Configuration

## URLs
### /api/v0/*$PROJECT*/deployment/

#### PUT
* **Response Type**: json
* **Response Example**: ```{"status": "created", "id": 1}```
* **Input Format**: None
* **Inputs**: None


## What's Happening

1. User requests a new job via the REST endpoint
2. The REST server creates a temporary response queue.
3. The REST server sends a message on the bus to exchange *releaseengine* on the topic *job.create*.
4. The REST server waits on the temporary response queue for a response.
5. Once a response is returned the REST service responds to the user with the job id.
6. The temporary response queue then is automatically deleted by the bus.
