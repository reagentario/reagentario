from app import db
from flask_user import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

    # User authentication information. The collation='NOCASE' is required
    # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
    email = db.Column(db.String(255), nullable=False, unique=True)
    email_confirmed_at = db.Column(db.DateTime())
    password = db.Column(db.String(255), nullable=False, server_default='')

    # User information
    alias = db.Column(db.String(3), nullable=False, unique=True)

    # Define the relationship to Role via UserRoles
    roles = db.relationship('Role', secondary='user_roles', backref=db.backref('users', lazy='dynamic'))

# Define the Role data-model
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

    def __repr__(self):
        return '<Role "{}">'.format(self.rolename)

# Define the UserRoles association table
class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))


class Locations(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True, unique=True)
    alias = db.Column(db.String(8), index=True, unique=True)

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), index=True, unique=False, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    location = db.relationship('Locations', backref='reagents', lazy='select')
    amount = db.Column(db.Integer, default=0)
    amount2 = db.Column(db.Integer, default=0)
    amount_limit = db.Column(db.Integer, default=0)
    size = db.Column(db.String(16), nullable=False)
    notes = db.Column(db.String(512))
    to_be_ordered = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<Reagent {}>'.format(self.name)

