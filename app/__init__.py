import os
import logging
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask.logging import create_logger
from flask_bootstrap import Bootstrap5
from flask_security.models import fsqla_v3 as fsqla
from flask_mailman import Mail

from .config import Config
logging.basicConfig(filename='logfile.log', level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
logw = logging.getLogger('werkzeug')
logw.setLevel(logging.ERROR)

# Create app
app = Flask(__name__)
log = create_logger(app)
app.config.from_object(Config)

bootstrap = Bootstrap5(app)

# Create database connection object
db = SQLAlchemy(app)

mail = Mail(app)

# Define models
fsqla.FsModels.set_db_info(db)

bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

from app import routes, models
from app.models import User
