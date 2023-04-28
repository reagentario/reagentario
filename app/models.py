from app import db
from app import login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_admin.contrib.sqla import ModelView
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

    # User authentication information. The collation='NOCASE' is required
    # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
    email = db.Column(db.String(255), nullable=False, unique=True)
    email_confirmed_at = db.Column(db.DateTime())
    password = db.Column(db.String(255))
    # User information
    alias = db.Column(db.String(3), nullable=False, unique=True)
    admin = db.Column(db.Boolean(), nullable=False, default=False)
    superadmin = db.Column(db.Boolean(), nullable=False, default=False)

    def __init__(self, email, password, alias):
        self.email = email
        self.password = generate_password_hash(password)
        self.alias = alias

    def set_password(self,password):
        self.password_hash = generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.password,password)

    def is_admin(self):
        return self.admin



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class Locations(db.Model):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True, unique=True)
    alias = db.Column(db.String(8), index=True, unique=True)
    #reagents = db.relationship('Inventory', backref='locations')

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

class Inventory(db.Model):
    __tablename__ = 'inventory'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), index=True, unique=False, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    location = db.relationship('Locations', backref='inventory')#, lazy='select')
    amount = db.Column(db.Integer, default=0)
    amount2 = db.Column(db.Integer, default=0)
    amount_limit = db.Column(db.Integer, default=0)
    size = db.Column(db.String(16), nullable=False)
    notes = db.Column(db.String(512))
    to_be_ordered = db.Column(db.Integer, default=0)

    def __repr__(self):
        return self.name #'<Reagent {}>'.format(self.name)

class InventoryView(ModelView):
    column_display_pk = True # optional, but I like to see the IDs in the list
    column_hide_backrefs = False
    #column_list = ('id', 'name', 'parent')

