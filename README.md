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
Configuration of the server is done in JSON and is by default kept in the current directories settings.json file.

You can override the location by setting `REREST_CONFIG` environment variable.

| Name     | Type | Parent | Value                                      |
|----------|------|--------|--------------------------------------------|
| LOGFILE  | str  | None   | File name for the application level log    |
| LOGLEVEL | str  | None   | DEBUG, INFO (default), WARN, FATAL         |
| MQ       | dict | None   | Where all of the MQ connection settins are |
| SERVER   | str  | MQ     | Hostname or IP of the server               |
| PORT     | int  | MQ     | Port to connect on                         |
| USER     | str  | MQ     | Username to connect with                   |
| PASSWORD | str  | MQ     | Password to authenticate with              |
| VHOST    | str  | MQ     | vhost on the server to utilize             |

Further configuration items can be found at http://flask.pocoo.org/docs/config/#builtin-configuration-values

### Example Config

```json
{
    "DEBUG": true,
    "PREFERRED_URL_SCHEME": "https",
    "LOGGER_NAME": "rerest",
    "LOGFILE": "rerest.log",
    "MQ": {
        "SERVER": "127.0.0.1",
        "PORT": 5672,
        "USER": "guest",
        "PASSWORD": "guest",
        "VHOST": "/"
    }
}
```

## URLs
### /api/v0/*$PROJECT*/deployment/

#### PUT
* **Response Type**: json
* **Response Example**: ```{"status": "created", "id": 1}```
* **Input Format**: None
* **Inputs**: None

## Depoloyment

### Apache with mod\_wsgi
mod_wsgi can be used with Apache to mount rerest. Example mod_wsgi files are located in contrib/mod_wsgi.

* rerest.conf: The mod_wsgi configuration file. This should be modified and placed in /etc/httpd/conf.d/.
* rerest.wsgi: The WSGI file that mod_wsgi will use. This should be modified and placed in the location noted in rerest.conf

### Gunicorn
Gunicorn (http://gunicorn.org/) is a popular open source Python WSGI server. It's still recommend to use Apache (or another web server) to handle auth before gunicorn since gunicorn itself is not set up for it.

```
$ gunicorn --user=YOUR_WORKER_USER --group=YOUR_WORKER_GROUP -D -b 127.0.0.1:5000 --access-logfile=/your/access.log --error-logfile=/your/error.log -e REREST_CONFIG=/full/path/to/settings.json rerest.app:app
```


## What's Happening

1. User requests a new job via the REST endpoint
2. The REST server creates a temporary response queue and binds it to the exchange with the same name.
3. The REST server sends a message on the bus to exchange *releaseengine* on the topic *job.create*.
4. The REST server waits on the temporary response queue for a response.
5. Once a response is returned the REST service responds to the user with the job id.
6. The temporary response queue then is automatically deleted by the bus.
