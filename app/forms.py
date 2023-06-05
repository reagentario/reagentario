from app import app
from app import db
from app.models import Inventory, Locations, User
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SubmitField, SelectField, IntegerField, ValidationError
from wtforms.validators import DataRequired, InputRequired, NumberRange, Email, EqualTo, Length

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
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
    name = StringField('Name', validators=[DataRequired(), Length(min=3, max=256)])
    location = LocationField('Locations',  validators=[InputRequired()])
    amount = IntegerField('Amount', validators=[NumberRange(min=0, max=1000000)])
    amount2 = IntegerField('Amount2', validators=[NumberRange(min=0, max=1000000)])
    size = StringField('Size', validators=[InputRequired(), Length(min=2, max=16)])
    amount_limit = IntegerField('Amount Limit', validators=[NumberRange(min=0, max=1000000)])
    notes = TextAreaField('Notes', render_kw={"rows": 4, "cols": 36}, validators=[Length(min=0, max=512)])
    to_be_ordered = IntegerField('To Be Ordered', validators=[NumberRange(min=0, max=1000)])
    submit = SubmitField()


class EditForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=3, max=256)])
    location = SelectField('Locations', validators=[InputRequired()], coerce=int)
    amount = IntegerField('Amount', validators=[NumberRange(min=0, max=1000000)])
    amount2 = IntegerField('Amount2', validators=[NumberRange(min=0, max=1000000)])
    size = StringField('Size', validators=[InputRequired(), Length(min=2, max=16)])
    amount_limit = IntegerField('Amount Limit', validators=[NumberRange(min=0, max=1000000)])
    notes = TextAreaField('Notes', render_kw={"rows": 4, "cols": 24}, validators=[Length(min=0, max=512)])
    to_be_ordered = IntegerField('To Be Ordered', validators=[NumberRange(min=0, max=1000)])
    submit = SubmitField('Save')
    cancel = SubmitField('Cancel')

class EditLocationForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired('Name is required'), Length(min=2, max=128)])
    short_name = StringField('Short Name', validators=[DataRequired('Short Name is required'), Length(min=1, max=8)])
    submit = SubmitField('Save')


class SearchForm(FlaskForm):
    name = StringField('Name')
    location = LocationField('Locations')

class EditProfileForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired('Email is required')])
    alias = StringField('Alias', validators=[DataRequired('Alias required')])
    admin = BooleanField('Admin')
    superadmin = BooleanField('Superadmin')
    submit = SubmitField('Save')


class ChangePasswordForm(FlaskForm):
      password = PasswordField('Password', validators=[DataRequired()])
      password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
      submit = SubmitField('Save')


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    alias = StringField('Alias', validators=[DataRequired('Alias required')])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_alias(self, alias):
        user = User.query.filter_by(alias=alias.data).first()
        if user is not None:
            raise ValidationError('Please use a different alias.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
