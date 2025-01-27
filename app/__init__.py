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
from flask_compress import Compress

from .config import Config
logging.basicConfig(filename='logfile.log', level=logging.ERROR, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
logw = logging.getLogger('werkzeug')
logw.setLevel(logging.ERROR)

# Create app
app = Flask(__name__)
log = create_logger(app)
app.config.from_object(Config)

# Initialize Flask-Compress
compress = Compress()
compress.init_app(app)

bootstrap = Bootstrap5(app)

# Create database connection object
db = SQLAlchemy(app)

mail = Mail(app)

# Define models
fsqla.FsModels.set_db_info(db)

bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

from app import models, reagent, user, location, department, errors, calibration
from app.models import User

@app.route("/")
@app.route("/index")
def index():
    """index"""
    return render_template("index.html")
