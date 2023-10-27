from app import db
from app import bcrypt
#from app import login_manager
from flask_admin.contrib.sqla import ModelView
from flask_security import UserMixin, RoleMixin
from sqlalchemy import Boolean, DateTime, Column, Integer, String, ForeignKey, UnicodeText
from sqlalchemy.orm import validates, relationship, backref

class RolesUsers(db.Model):
    __tablename__ = "roles_users"
    __table_args__ = {'extend_existing': True}
    id = db.Column(Integer(), primary_key=True)
    user_id = db.Column("user_id", Integer(), ForeignKey("user.id"))
    role_id = db.Column("role_id", Integer(), ForeignKey("role.id"))


class Role(db.Model, RoleMixin):
    __tablename__ = "role"
    id = db.Column(Integer(), primary_key=True)
    name = db.Column(String(80), unique=True)
    description = db.Column(String(255))
    permissions = db.Column(UnicodeText)


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(Integer, primary_key=True)
    email = db.Column(String(255), unique=True, nullable=False)
    username = db.Column(String(64), unique=True)
    password = db.Column(String(255), nullable=False)
    last_login_at = db.Column(DateTime())
    current_login_at = db.Column(DateTime())
    last_login_ip = db.Column(String(100))
    current_login_ip = db.Column(String(100))
    login_count = db.Column(Integer)
    active = db.Column(Boolean(), nullable=False, default=False)
    fs_uniquifier = db.Column(String(64), unique=True, nullable=False)
    confirmed_at = db.Column(DateTime())
    roles = relationship('Role', secondary='roles_users',
                         backref=backref('users', lazy='dynamic'))


    @validates('email')
    def validate_email(self, key, address):
        if '@' not in address:
            raise ValueError("Failed simple email validation")
        return address

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password)

    def check_password_hash(self, password):
        return bcrypt.check_password_hash(self.password, password)

    @property
    def is_active(self):
        return self.active

    def __repr__(self):
        return self.username


class Locations(db.Model):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True, unique=True)
    short_name = db.Column(db.String(8), index=True, unique=True)

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class Inventory(db.Model):
    __tablename__ = 'inventory'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), index=True, unique=False, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    location = db.relationship('Locations', backref='location', lazy=True)
    amount = db.Column(db.Integer, default=0)
    amount2 = db.Column(db.Integer, default=0)
    amount_limit = db.Column(db.Integer, default=0)
    size = db.Column(db.String(16), nullable=False)
    notes = db.Column(db.String(512))
    order = db.Column(db.Integer, default=0)

    def __repr__(self):
        return self.name #'<Reagent {}>'.format(self.name)


class Applog(db.Model):
    __tablename__ = 'applog'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='user', lazy=True)
    product_id = db.Column(db.Integer, db.ForeignKey('inventory.id'))
    product = db.relationship('Inventory', backref='log', lazy=True)
    event_time = db.Column(db.DateTime)
    event_detail = db.Column(db.String(512))

    def __repr__(self):
          return self.event_detail


class InventoryView(ModelView):
    column_display_pk = True # optional, to see the IDs in the list
    column_hide_backrefs = True
    column_list = ('id', 'name', 'location', 'amount', 'amount2', 'amount_limit', 'size', 'notes', 'to_be_ordered')
    form_excluded_columns = ('log')


class UserView(ModelView):
    column_display_pk = True # optional, to see the IDs in the list
    column_exclude_list = ['password', ]
    form_excluded_columns = ('password')
