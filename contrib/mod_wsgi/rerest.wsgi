import os

os.environ['REREST_CONFIG'] = '/path/to/rerest/settings.json'

from rerest.app import app as application
