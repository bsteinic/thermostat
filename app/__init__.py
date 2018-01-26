from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
def enable_global_distpackages():
  import sys
  sys.path.append('/usr/lib/python2.7/dist-packages')
  sys.path.append('/usr/local/lib/python2.7/dist-packages')

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

from app import views, models

enable_global_distpackages()

