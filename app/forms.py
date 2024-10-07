from app import app
from app import db
from app.models import Inventory, Locations, Departments, User
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SubmitField, SelectField, IntegerField, ValidationError, DateField
from wtforms.validators import DataRequired, InputRequired, NumberRange, Email, EqualTo, Length

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
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


class DepartmentField(SelectField):
    def iter_choices(self):
        departments = [("", "")]
        departments += [(l.id, l.name) for l in Departments.query.all()]
        for value, label in departments:
            yield (value, label, self.coerce(value) == self.data)
    def pre_validate(self, form):
        for v, _ in [(l.id, l.name) for l in Departments.query.all()]:
            if self.data == v:
                break
            else:
                raise ValueError(self.gettext('Not a valid choice'))


class CreateForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=3, max=256)])
    location = LocationField('Location',  validators=[InputRequired()])
    amount = IntegerField('Amount in lab', validators=[NumberRange(min=0, max=1000000)])
    amount2 = IntegerField('Amount in warehouse', validators=[NumberRange(min=0, max=1000000)])
    size = StringField('Size', validators=[Length(max=16)])
    amount_limit = IntegerField('Minimum stock', validators=[NumberRange(min=0, max=1000000)])
    product_code = StringField('Product Code', validators=[Length(max=64)])
    supplier = StringField('Supplier', validators=[Length(max=64)])
    batch = StringField('Batch', validators=[Length(max=64)])
    expiry_date = StringField('Expiry Date', validators=[Length(max=16)])
    notes = TextAreaField('Notes', render_kw={"rows": 4, "cols": 36}, validators=[Length(min=0, max=512)])
    order = IntegerField('Order', validators=[NumberRange(min=0, max=1000)])
    submit = SubmitField()


class CreateLocationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=3, max=256)])
    short_name = StringField('Short Name', validators=[DataRequired('Short Name is required'), Length(min=1, max=8)])
    department = DepartmentField('Department',  validators=[InputRequired()])
    submit = SubmitField()


class CreateCalibrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=256)])
    apparatus = StringField('Apparatus', validators=[DataRequired(), Length(min=0, max=256)])
    description = StringField('Description', validators=[Length(min=0, max=256)])
    department = DepartmentField('Department',  validators=[InputRequired()])
    initial_check_date = DateField('Initial Check Date', validators=[InputRequired()])
    frequency = IntegerField('Frequency', validators=[DataRequired()])
    frequency_units = SelectField('Frequency Unit', choices=[
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years')
    ])
    tolerance = IntegerField('Tolerance', validators=[DataRequired()])
    tolerance_units = SelectField('Tolerance Unit', choices=[
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years')
    ])
    last_calibration_date = DateField('Last Calibration Date', validators=[InputRequired()])
    notes = StringField('Notes', validators=[Length(min=0, max=512)])
    submit = SubmitField()


class EditForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=3, max=256)])
    location = SelectField('Location', validators=[InputRequired()], coerce=int)
    amount = IntegerField('Amount in lab', validators=[NumberRange(min=0, max=1000000)])
    amount2 = IntegerField('Amount in warehouse', validators=[NumberRange(min=0, max=1000000)])
    size = StringField('Size', validators=[Length(max=16)])
    amount_limit = IntegerField('Minimum stock', validators=[NumberRange(min=0, max=1000000)])
    product_code = StringField('Product Code', validators=[Length(max=64)])
    supplier = StringField('Supplier', validators=[Length(max=64)])
    batch = StringField('Batch', validators=[Length(max=64)])
    expiry_date = StringField('Expiry Date', validators=[Length(max=16)])
    notes = TextAreaField('Notes', render_kw={"rows": 4, "cols": 24}, validators=[Length(min=0, max=512)])
    order = IntegerField('Order', validators=[NumberRange(min=0, max=1000)])
    submit = SubmitField('Save')
    cancel = SubmitField('Cancel')


class EditLocationForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired('Name is required'), Length(min=2, max=128)])
    short_name = StringField('Short Name', validators=[DataRequired('Short Name is required'), Length(min=1, max=8)])
    department = SelectField('Department', validators=[InputRequired()], coerce=int)
    submit = SubmitField('Save')


class EditCalibrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=256)])
    apparatus = StringField('Apparatus', validators=[DataRequired(), Length(min=0, max=256)])
    description = StringField('Description', validators=[Length(min=0, max=256)])
    department = SelectField('Department',  validators=[InputRequired()], coerce=int)
    initial_check_date = DateField('Initial Check Date', validators=[InputRequired()])
    frequency = IntegerField('Frequency', validators=[DataRequired()])
    frequency_units = SelectField('Frequency Unit', choices=[
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years')
    ])
    tolerance = IntegerField('Tolerance', validators=[DataRequired()])
    tolerance_units = SelectField('Tolerance Unit', choices=[
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years')
    ])
    last_calibration_date = DateField('Last Calibration Date')
    #next_calibration_date = DateField('Next Calibration Date')
    notes = StringField('Notes', validators=[Length(min=0, max=512)])
    submit = SubmitField('Save')
    cancel = SubmitField('Cancel')


class EditDepartmentForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired('Name is required'), Length(min=2, max=128)])
    short_name = StringField('Short Name', validators=[DataRequired('Short Name is required'), Length(min=1, max=8)])
    submit = SubmitField('Save')


class SearchForm(FlaskForm):
    name = StringField('Name')
    location = LocationField('Locations')


class EditProfileForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired('Email is required'), Email()])
    username = StringField('Username', validators=[DataRequired('Username is required'), Length(min=2, max=64)])
    active = BooleanField('Active')
    submit = SubmitField('Save')
    cancel = SubmitField('Cancel')


class EditRolesForm(FlaskForm):
    admin = BooleanField('Admin')
    superadmin = BooleanField('Superadmin')
    qc = BooleanField('QC')
    vl = BooleanField('VL')
    submit = SubmitField('Save')
    cancel = SubmitField('Cancel')


class CreateUserForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired('Email is required'), Email()])
    username = StringField('Username', validators=[DataRequired('Username is required'), Length(min=2, max=64)])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    admin = BooleanField('Admin', default=False)
    superadmin = BooleanField('Superadmin', default=False)
    qc = BooleanField('QC', default=False)
    vl = BooleanField('VL', default=False)
    submit = SubmitField('Save')


class ChangePasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Save')
    cancel = SubmitField('Cancel')


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired('Email is required'), Email()])
    username = StringField('Username', validators=[DataRequired('Username is required'), Length(min=2, max=64)])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    cancel = SubmitField('Cancel')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username already in use, choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email address already registered.')
