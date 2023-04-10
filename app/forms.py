from app import db
from app.models import Inventory, Locations
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, InputRequired, NumberRange

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class LocationField(SelectField):
    def iter_choices(self):
        locations = [("", "")]
        locations += [(l.id, l.name) for l in Locations.query.all()]
        for value, label in locations:
            yield (value, label, self.coerce(value) == self.data)
    def pre_validate(self, form):
        for v, _ in [(l.id, l.name) for l in Locations.query.all()]:
            if self.data == v:
                break
            else:
                raise ValueError(self.gettext('Not a valid choice'))

class CreateForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired()])
    location = LocationField('Locations')
    amount = IntegerField('Amount', validators=[NumberRange(min=0, max=None)])
    amount2 = IntegerField('Amount2', validators=[NumberRange(min=0, max=None)])
    size = StringField('Size', validators=[InputRequired()])
    amount_limit = StringField('Amount Limit', validators=[NumberRange(min=0, max=None)])
    notes = StringField('Notes')
    to_be_ordered = IntegerField('To Be Ordered', validators=[NumberRange(min=0, max=None)])


class SearchForm(FlaskForm):
    name = StringField('Name')
    location = LocationField('Locations')


# Define the User profile form
class EditProfileForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired('Email is required')])
    alias = StringField('Alias', validators=[DataRequired('Alias required')])

    submit = SubmitField('Save')
