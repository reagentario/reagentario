import os
from flask import Flask, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, auth_required, hash_password
from flask_security.models import fsqla_v3 as fsqla

from .config import Config

# Create app
app = Flask(__name__)

app.config.from_object(Config)

# Create database connection object
db = SQLAlchemy(app)

# Define models
fsqla.FsModels.set_db_info(db)

from .models import Inventory, Locations, User, Role, InventoryView, UserView, Applog

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
app.security = Security(app, user_datastore)

# Views
@app.route("/")
@auth_required()
def home():
    return render_template_string("Hello {{ current_user.email }}")

# one time setup
with app.app_context():
    # Create User to test with
    db.create_all()
    if not app.security.datastore.find_user(email="test@me.com"):
        app.security.datastore.create_user(email="test@me.com", password=hash_password("password"))
    db.session.commit()

if __name__ == '__main__':
    app.run()
