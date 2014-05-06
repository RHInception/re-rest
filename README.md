# RE-REST
Simple REST Api for our new [release engine hotness](https://github.com/RHInception/?query=re-)

[![Build Status](https://api.travis-ci.org/RHInception/re-rest.png)](https://travis-ci.org/RHInception/re-rest/)

## Running From Source
To run directly from source in order to test out the server run:

```bash
$ python rundevserver.py
```

The dev server will allow any HTTP Basic Auth user/password combination.


## Unittests
Use *nosetests -v --with-cover --cover-min-percentage=80 --cover-package=rerest test/* from the main directory to execute unittests.

## Configuration
Configuration of the server is done in JSON and is by default kept in the current directories settings.json file.

You can override the location by setting `REREST_CONFIG` environment variable.

| Name              | Type | Parent            | Value                                      |
|-------------------|------|-------------------|--------------------------------------------|
| LOGFILE           | str  | None              | File name for the application level log    |
| LOGLEVEL          | str  | None              | DEBUG, INFO (default), WARN, FATAL         |
| MQ                | dict | None              | Where all of the MQ connection settins are |
| SERVER            | str  | MQ                | Hostname or IP of the server               |
| PORT              | int  | MQ                | Port to connect on                         |
| USER              | str  | MQ                | Username to connect with                   |
| PASSWORD          | str  | MQ                | Password to authenticate with              |
| VHOST             | str  | MQ                | vhost on the server to utilize             |
| MONGODB\_SETTINGS | dict | None              | Where all of the MongoDB settings live     |
| DB                | str  | MONGODB\_Settings | Name of the database to use                |
| USERNAME          | str  | MONGODB\_Settings | Username to auth with                      |
| Password          | str  | MONGODB\_Settings | Password to auth with                      |
| HOST              | str  | MONGODB\_Settings | Host to connect to                         |
| PORT              | int  | MONGODB\_Settings | Port to connect to on the host             |

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
    },
    "MONGODB_SETTINGS": {
        "DB": "re",
        "USERNAME": "username",
        "PASSWORD": "password",
        "HOST": "127.0.0.1",
        "PORT": 27017
    }
}
```

## URLs
### /api/v0/*$PROJECT*/deployment/

#### PUT
Creates a new deployment.

* **Response Type**: json
* **Response Example**: ```{"status": "created", "id": 1}```
* **Input Format**: None
* **Inputs**: optional json

### /api/v0/playbooks/

#### GET
Gets a list of **all** playbooks.

* **Response Type**: json
* **Response Example**: ```{"status": "ok", "items": [...]}```
* **Input Format**: None
* **Inputs**: None


### /api/v0/*$PROJECT*/playbook/

#### GET
Gets a list of all playbooks for a project.

* **Response Type**: json
* **Response Example**: ```{"status": "ok", "items": [...]}```
* **Input Format**: None
* **Inputs**: None

#### PUT
Creates a new playbook.

* **Response Type**: json
* **Response Example**: ```{"status": "created", "id": "53614ccf1370129d6f29c7dd"}```
* **Input Format**: json
* **Inputs**: **TODO**

### /api/v0/*$PROJECT*/playbook/*$ID*/

#### GET
Gets a playbooks for a project.

* **Response Type**: json
* **Response Example**: ```{"status": "ok", "item": ...}```
* **Input Format**: None
* **Inputs**: None

#### POST
Replace a playbook in a project.

* **Response Type**: json
* **Response Example**: ```{"status": "ok", "id": "53614ccf1370129d6f29c7dd"}```
* **Input Format**: json
* **Inputs**: **TODO**

#### DELETE
Delete a playbook in a project.

* **Response Type**: json
* **Response Example**: ```{"status": "gone"}```
* **Input Format**: None
* **Inputs**: None


## Deployment

### Apache with mod\_wsgi
mod_wsgi can be used with Apache to mount rerest. Example mod_wsgi files are located in contrib/mod_wsgi.

* rerest.conf: The mod_wsgi configuration file. This should be modified and placed in /etc/httpd/conf.d/.
* rerest.wsgi: The WSGI file that mod_wsgi will use. This should be modified and placed in the location noted in rerest.conf

### Gunicorn
Gunicorn (http://gunicorn.org/) is a popular open source Python WSGI server. It's still recommend to use Apache (or another web server) to handle auth before gunicorn since gunicorn itself is not set up for it.

```bash
$ gunicorn --user=YOUR_WORKER_USER --group=YOUR_WORKER_GROUP -D -b 127.0.0.1:5000 --access-logfile=/your/access.log --error-logfile=/your/error.log -e REREST_CONFIG=/full/path/to/settings.json rerest.app:app
```

## Authentication
re-rest uses a simple decorater which enforces a REMOTE\_USER be set.

### rerest.decorators:remote\_user\_required
This decorator assumes that re-rest is running behind another web server which is taking care of authentication. If REMOTE\_USER is passed to re-rest from the web server re-rest assumes authentication has succeeded. If it is not passed through re-rest treats the users as unauthenticated.

**WARNING**: When using this decorator it is very important that re-rest not be reachable by any means other than through the front end webserver!!


### Platform Gotcha's

#### RHEL 6
You may need to add the following to your PYTHONPATH to be able to use Jinja2:

```
/usr/lib/python2.6/site-packages/Jinja2-2.6-py2.6.egg
```

## What's Happening

1. User requests a new job via the REST endpoint
2. The REST server creates a temporary response queue and binds it to the exchange with the same name.
3. The REST server creates a message with a reply_to of the temporary response queue's topic.
4. The REST server sends the message to the bus on exchange *re* and topic *job.create*. Body Example: ```{"project": "nameofproject"}```
5. The REST server waits on the temporary response queue for a response.
6. Once a response is returned the REST service loads the body into a json structure and pulls out the id parameter.
7. The REST service then responds to the user with the job id.
8. The temporary response queue then is automatically deleted by the bus.


## Usage Example
The authentication mechanism used in the front end webserver could be set up to use vastly different schemes. Instead of covering every possible authentication style which could be used we will work with two common ones in usage examples: htacces and kerberos.

*Note*: Setting up the front end proxy server for authentication is out of scope for this documentation.

### htaccess / HTTP Basic Auth
```
$ curl -X PUT --user "USERNAME" https://rerest.example.com/api/v0/test/deployment/
Password:
... # 201 and json data if exists, otherwise an error code
```

### kerberos
```
$ kinit -f USERNAME
Password for USERNAME@DOMAIN:
$ curl --negotiate -u 'a:a' policy -X PUT https://rerest.example.com/api/v0/test/deployment/

... # 201 and json data if exists, otherwise an error code
```

### Dynamic Variables
Passing dynamic variables requires two additions

1. We must set the ``Content-Type`` header (``-H ...`` below) to ``application/json``
2. We must pass **data** (``-d '{....}'`` below) for the ``PUT`` to send to the server

This example sets the ``Content-Type`` and passes two **dynamic
variables**: ``cart`` which is the name of a
[Juicer](https://github.com/juicer/juicer) release cart, and
``environment``, which is the environment to push the release cart
contents to.

```
$ curl -H "Content-Type: application/json" -d '{"cart": "bitmath", "environment": "re"}' -X PUT http://rerest.example.com/api/v0/test/deployment/

... # 201 and json data if exists, otherwise an error code
```
