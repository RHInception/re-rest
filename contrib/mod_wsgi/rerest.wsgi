import os

os.environ['REREST_CONFIG'] = '/path/to/cacophony/settings.json'

from rerest.app import app as application
