from datetime import datetime
from flask import render_template, make_response, flash, redirect, url_for, request, session
from flask_login import current_user, login_user, logout_user, login_required
from app import app
from app import db
from app import bcrypt
from app import log
from app.forms import LoginForm, CreateForm, SearchForm, EditForm, EditProfileForm, ChangePasswordForm, EditLocationForm, RegistrationForm
from app.models import Inventory, Locations, User, InventoryView, UserView, Applog

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.ajax import QueryAjaxModelLoader
from flask_admin.model import BaseModelView
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.functions import add_log

admin = Admin(app, name='reagentario', template_mode='bootstrap3')
admin.add_view(UserView(User, db.session))
admin.add_view(InventoryView(Inventory, db.session))
admin.add_view(ModelView(Locations, db.session))


@app.route('/c')
def c():
    with app.app_context():

        # Create 'member@example.com' user with no roles
        if not User.query.filter(User.email == 'member@example.com').first():
            user = User(
                email='member@example.com',
                password='Password1',
                alias='ME'
            )
            db.session.add(user)
            db.session.commit()

        # Create 'admin@example.com' user with 'Admin' and 'Agent' roles
        if not User.query.filter(User.email == 'admin3@example.com').first():
            user = User(
                email='admin3@example.com',
                password='Password1',
                alias='A3'
            )
            if not user.check_password_hash('Password1'):
                log.debug("ERROR creating user admin")
                return render_template('index.html')
            log.debug("created user admin")
            user.admin = True
            user.superadmin = True
            db.session.add(user)
            db.session.commit()

    return render_template('index.html')


@app.route('/')
@app.route('/index')
def index():
    """ index """
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """ login form """
    if current_user.is_authenticated:
        flash('You are already logged in', 'info')
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        email = request.form.get('email')
        password = request.form.get('password')
        existing_user = User.query.filter_by(email=email).first()
        if not existing_user:
            flash('Invalid username ' + str(email), 'danger')
            return render_template('login.html', title='Sign In', form=form)
        if not existing_user.check_password_hash(password):
            flash('Invalid password. Please try again.', 'danger')
            return render_template('login.html', title='Sign In', form=form)
        login_user(existing_user, remember=form.remember_me.data)
        flash('You have successfully logged in.', 'success')
        return redirect(url_for('index'))
    if form.errors:
        flash(form.errors, 'danger')
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    """ logout """
    logout_user()
    flash('You have successfully logged out.', 'success')
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, alias=form.alias.data, password=form.password.data, )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """ edit profile form """
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.email = form.email.data
        current_user.alias = form.alias.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    if request.method == 'GET':
        form.email.data = current_user.email
        form.alias.data = current_user.alias

    return render_template('edit_profile.html', title='Edit Profile',
                           form=form, user=current_user)


@app.route('/edit_user/<alias>', methods=['GET', 'POST'])
@login_required
def edit_user(alias):
    """ edit user form """
    if current_user.alias == alias or current_user.is_superadmin:
        form = EditProfileForm()
        user = User.query.filter_by(alias=alias).first()
        if not user:
            flash('Not existing user alias ' + alias, 'danger')
            return redirect(url_for('index'))
        if form.validate_on_submit():
            user.email = form.email.data
            user.alias = form.alias.data
            user.admin = form.admin.data
            user.superadmin = form.superadmin.data
            db.session.commit()
            flash('Your changes have been saved.')
            return redirect(url_for('users'))
        if request.method == 'GET':
            form.email.data = user.email
            form.alias.data = user.alias
            form.admin.data = user.admin
            form.superadmin.data = user.superadmin
        return render_template('edit_user.html', title='Edit Profile',
                               form=form, user=user)
    else:
        flash('You cannot change data for user {}'.format(alias), 'danger')
        return redirect(url_for('users'))



@app.route('/change_pw/<alias>', methods=['GET', 'POST'])
@login_required
def change_pw(alias):
    """ change password form """
    if current_user.alias == alias or current_user.is_superadmin:
        form = ChangePasswordForm()
        user = User.query.filter_by(alias=alias).first()
        if not user:
            flash('Not existing user alias ' + alias, 'danger')
            return redirect(url_for('index'))
        if form.validate_on_submit():
            user.password = bcrypt.generate_password_hash(form.password.data)
            flash('Password changed for ' + alias, 'info')
            db.session.commit()
            return redirect(url_for('index'))
        return render_template('change_pw.html', title='Change Password',
                           form=form, user=user)
    else:
        flash('You cannot change the password for user {}'.format(alias), 'danger')
        return redirect(url_for('index'))


@app.route('/users', methods=['GET'])
@login_required
def users():
    if not current_user.is_admin:
        return render_template('401.html')
    _users = User.query.all()
    return render_template('users.html', users=_users)


@app.route('/list', methods=['GET', 'POST'])
def list():
    """ list all reagents """
    form = SearchForm(csrf_enabled=False)

    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']  #Locations.query.get_or_404(form.location.data)
        reagents = Inventory.query.filter(db.and_(Inventory.name.like('%'+name+'%'), Inventory.location_id.like('%'+form.location.data+'%'))).all()
        msg = location
        return render_template('list.html', form=form, reagents=reagents, warning=msg)

    if request.method == 'GET':
        reagents = Inventory.query.all()

    if len(reagents) > 0:
        flash("Number of reagents: " + str(len(reagents)), 'info')
        return render_template('list.html', form=form, reagents=reagents)
    flash("No Reagents Found!")
    msg = 'No Reagents Found'
    return render_template('list.html', form=form, warning=msg)


@app.route('/list_locations', methods=['GET'])
def list_locations():
    """ list all locations """
    locations = Locations.query.all()

    if len(locations) > 0:
        return render_template('list_locations.html', locations=locations)
    flash("No Locations Found!")
    msg = 'No Locations Found'
    return render_template('list_locations.html', warning=msg)


@app.route('/edit_location/<int:id>/', methods=['GET', 'POST'])
@login_required
def edit_location(id):
    """ edit location form """
    form = EditLocationForm()
    location = db.session.query(Locations).filter(Locations.id == id).first()

    if form.validate_on_submit():
        location.name = form.name.data
        location.short_name = form.short_name.data
        existing_location = Locations.query.filter(Locations.name == location.name or Locations.short_name == location.short_name).first()
        if existing_location:
            # https://getbootstrap.com/docs/5.0/components/alerts/ colors
            flash('A Location with this name ({}) or short_name ({}) already exists!'.format(location.name, location.short_name), 'danger')
            return render_template('edit_location.html', title='Edit Location', id=id, form=form)
        try:
            db.session.commit()
            flash('Your changes have been saved.')
            return redirect(url_for('list_locations'))
        except Exception as e:
            flash('Error editing {} with error {}'.format(location.id, str(e)), 'danger')
            db.session.rollback()
            return render_template('edit_location.html', title='Edit Location',
                                   id=id, form=form)
    if request.method == 'GET':
        form.name.data = location.name
        form.short_name.data = location.short_name
        return render_template('edit_location.html', title='Edit Location',
                            id=id, form=form)
    return redirect(url_for('list_locations'))


@app.route('/list_location_content/<int:_id>/', methods=['GET', 'POST'])
def list_location_content(_id):
    """ list content of a location """
    reagents = Inventory.query.filter(Inventory.location_id==_id).all()
    location = Locations.query.filter(Locations.id==_id).first()
    loc_name = location.name

    if len(reagents) > 0:
        flash("Number of reagents: " + str(len(reagents)), 'info')
        return render_template('list.html', title=loc_name, reagents=reagents)
    flash("No Reagents Found!")
    msg = 'No Reagents Found in this location'
    return render_template('list.html', title=loc_name, warning=msg)


@app.route('/show/<int:id>/')
def show(id):
    """ show a specific reagent """
    reagent = Inventory.query.get_or_404(id)
    return render_template('show.html', title=reagent.name, reagent=reagent)


@app.route('/edit/<int:id>/', methods=['GET', 'POST'])
def edit(id):
    """ edit a specific reagent"""
    reag = db.session.query(Inventory).filter(Inventory.id == id).first()
    loc = [(loc.id, loc.name) for loc in Locations.query.all()]
    form = EditForm(csrf_enabled=False, exclude_fk=False, obj=reag)
    form.location.choices = loc
    form.location.data=reag.location.id
    r1 = reag.__dict__.copy()

    if form.validate_on_submit():
        loc_selected = request.form['location']
        reag.name = request.form['name']
        reag.location = Locations.query.get(loc_selected)
        reag.amount = request.form['amount']
        reag.amount2 = request.form['amount2']
        reag.size = request.form['size']
        reag.amount_limit = request.form['amount_limit']
        reag.notes = request.form['notes']
        reag.to_be_ordered = request.form['to_be_ordered']

        r2 = reag.__dict__.copy()
        k1 = set(r1.keys())
        k2 = set(r2.keys())
        common_keys = set(k1).intersection(set(k2))
        try:
            log.debug("updating id %s", reag.id)
            db.session.commit()
            for key in common_keys:
                if str(r1[key]) != str(r2[key]):
                    add_log(reag.id, current_user.id, 'updated item %s - %s: %s value changed from "%s" to "%s"' % (reag.id, reag.name, key, str(r1[key]), str(r2[key])))
                    log.debug('updated item %s - %s: %s value changed from "%s" to "%s"' % (reag.id, reag.name, key, str(r1[key]), str(r2[key])))

        except Exception as e:
            flash('Error updating %s' % str(e), 'danger')
            log.debug("ERROR not updated id %s", reag.id)
            db.session.rollback()
        else:
            flash('Item updated', 'info')
        return redirect(url_for('show', id=id))

    flash('Error on form validation', 'danger')

    return render_template('edit.html', id=id, form=form)


@app.route('/delete/<int:id>/', methods=['GET'])
def delete(id):
    """ delete a specific reagent """
    reagent = db.session.query(Inventory).filter(Inventory.id == id).first()
    if reagent:
        try:
            db.session.delete(reagent)
            db.session.commit()
            add_log(reagent.id, current_user.id, 'deleted item %s - %s' % (reagent.id, reagent.name))
            flash("Item deleted")
            log.debug("deleted id %s", reagent.id)
        except Exception as e:
            flash('Error deleting {} with error {}'.format(reagent.id, str(e)), 'danger')
            log.debug("ERROR not deleted id %s", reagent.id)
            db.session.rollback()
    else:
        flash('Error deleting product with id: ' + str(id), 'danger')
        return redirect(url_for('show', id=id))
    return redirect(url_for('list'))


@app.route('/create_location', methods=['GET', 'POST'])
def create_location():
    """ create a new location form """
    if request.method == 'POST':
        name = request.form['name']
        short_name = request.form['short_name']
        location = Locations(name=name,
                          short_name=short_name)
        existing_location = Locations.query.filter(
            Locations.name == name or Locations.short_name == short_name
        ).first()
        if existing_location:
            # https://getbootstrap.com/docs/5.0/components/alerts/ colors
            flash('A Location with this name ({}) or short_name ({}) already exists!'.format(name, short_name), 'danger')
            return render_template('create_location.html')
        db.session.add(location)
        db.session.commit()

        return redirect(url_for('list_locations'))
    return render_template('create_location.html')


@app.route('/delete_location/<int:id>/', methods=['GET'])
def delete_location(id):
    """ delete a specific reagent """
    location = db.session.query(Locations).filter(Locations.id == id).first()
    if location:
        reagents_in = Inventory.query.filter(Inventory.location_id==id).all()
        if len(reagents_in) > 0:
            flash("Location %s contains some reagents, it cannot be deleted" % location.name, 'danger')
            return redirect(url_for('list_locations'))
        try:
            db.session.delete(location)
            db.session.commit()
            add_log(location.id, current_user.id, 'deleted location %s - %s' % (location.id, location.name))
            flash("Location deleted")
            log.debug("deleted location id %s", location.id)
        except Exception as e:
            flash('Error deleting {} with error {}'.format(location.id, str(e)), 'danger')
            log.debug("ERROR not deleted location id %s", location.id)
            db.session.rollback()
    else:
        flash('Error deleting location with id: ' + str(id), 'danger')
        return redirect(url_for('list_locations'))
    return redirect(url_for('list_locations'))



@app.route('/create', methods=['GET', 'POST'])
def create():
    """ create a new reagent form """
    form = CreateForm(csrf_enabled=False)
    form.amount.data=0
    form.amount2.data=0
    form.amount_limit.data=0
    form.to_be_ordered.data=0

    if request.method == 'POST':
        name = request.form['name']
        location = Locations.query.get_or_404(form.location.data)
        amount = request.form['amount']
        amount2 = request.form['amount2']
        size = request.form['size']
        amount_limit = request.form['amount_limit']
        notes = request.form['notes']
        to_be_ordered = request.form['to_be_ordered']
        reagent = Inventory(name=name,
                          location=location,
                          amount=amount,
                          amount2=amount2,
                          size=size,
                          amount_limit=amount_limit,
                          notes=notes,
                          to_be_ordered=to_be_ordered)
        db.session.add(reagent)
        db.session.commit()
        db.session.refresh(reagent)
        add_log(reagent.id, current_user.id, 'created item %s - %s' % (reagent.id, reagent.name))
        return redirect(url_for('list'))

    return render_template('create.html', form=form)


@app.route('/order/<int:id>/', methods=['GET'])
def order(id):
    """ set order for a reagent """
    reagent = db.session.query(Inventory).filter(Inventory.id == id).first()
    if reagent:
        reagent.to_be_ordered += 1
        try:
            db.session.commit()
            flash("Item ordered")
            add_log(reagent.id, current_user.id, 'ordered item %s - %s' %
                   (reagent.id, reagent.name))
            log.debug("ordered id %s", reagent.id)
        except Exception as e:
            flash('Error ordering {} with error {}'.format(reagent.id, str(e)), 'danger')
            log.debug("ERROR ordefing id %s", reagent.id)
            db.session.rollback()
    else:
        flash('Error ordering product with id: ' + str(id), 'danger')
        return redirect(url_for('show', id=id))
    return redirect(url_for('show', id=id))


@app.route('/view_orders/', methods=['GET'])
def view_orders():
    """ view orders """
    orders = db.session.query(Inventory).filter(Inventory.to_be_ordered > 0)
    if orders.count() > 0:
        return render_template('view_orders.html', reagents=orders)
    flash('No orders pending', 'info')
    return  render_template('view_orders.html', reagents=orders)


@app.route('/reset_order/<int:id>/', methods=['GET'])
def reset_order(id):
    """ reset order for a specific reagent """
    reagent = db.session.query(Inventory).filter(Inventory.id == id).first()
    if reagent:
        reagent.to_be_ordered = 0
        try:
            db.session.commit()
            flash("Item orders reset")
            add_log(reagent.id, current_user.id, 'reset orders for item %s - %s' % (reagent.id, reagent.name))
            log.debug("reset orders for id %s", reagent.id)
        except Exception as e:
            flash('Error reset ordering {} with error {}'.format(reagent.id, str(e)), 'danger')
            log.debug("ERROR resetting order id %s", reagent.id)
            db.session.rollback()
    else:
        flash('Error resetting order product with id: ' + str(id), 'danger')
        return redirect(url_for('show', id=id))
    return redirect(url_for('view_orders'))


@app.route('/view_low_quantity/', methods=['GET'])
def view_low_quantity():
    """ view list of reagent with low quantity """
    reag = db.session.query(Inventory).filter((Inventory.amount+Inventory.amount2)<Inventory.amount_limit)
    if reag.count() > 0:
        return render_template('list.html', reagents=reag, title="Low Quantity")
    flash('No reagents below quantity limits', 'info')
    return  render_template('list.html', reagents=reag)


@app.route('/plus/<int:id>/')
def plus(id):
    """ add 1 item of a specific reagent in lab """
    reagent = Inventory.query.get_or_404(id)
    reagent.amount += 1
    db.session.commit()
    add_log(reagent.id, current_user.id, 'added item %s - %s' % (reagent.id, reagent.name))
    return redirect(url_for('show', id = id))


@app.route('/minus/<int:id>/')
def minus(id):
    """ remove 1 item of a specific reagent in lab """
    reagent = Inventory.query.get_or_404(id)
    if reagent.amount == 0:
        flash("No Reagents Found!")
        return redirect(url_for('show', id = id))
    reagent.amount -= 1
    db.session.commit()
    add_log(reagent.id, current_user.id, 'removed item %s - %s' % (reagent.id, reagent.name))

    return redirect(url_for('show', id = id))


@app.route('/move/<int:id>/')
def move(id):
    """ move 1 item of a specific reagent from warehouse to lab """
    reagent = Inventory.query.get_or_404(id)
    if reagent.amount2 == 0:
        flash("No more items available in the warehouse", 'danger')
        return redirect(url_for('show', id = id))
    else:
        reagent.amount2 -=1
        reagent.amount +=1
        db.session.commit()
        add_log(reagent.id, current_user.id, 'moved from warehouse item %s - %s' % (reagent.id, reagent.name))
        return redirect(url_for('show', id = id))


@app.route('/add/<int:id>/')
def add(id):
    """ add 1 item of a specific reagent to warehouse """
    reagent = Inventory.query.get_or_404(id)
    reagent.amount2 += 1
    db.session.commit()
    add_log(reagent.id, current_user.id, 'added to warehouse item %s - %s' % (reagent.id, reagent.name))
    return redirect(url_for('show', id = id))


@app.route('/show_log/<int:id>/')
def show_log(id):
    """ list logs """
    #form = SearchForm(csrf_enabled=False)

    #if request.method == 'POST':
    #    name = request.form['name']
    #    location = request.form['location']  #Locations.query.get_or_404(form.location.data)
    #    reagents = Inventory.query.filter(db.and_(Inventory.name.like('%'+name+'%'), Inventory.location_id.like('%'+form.location.data+'%'))).all()
    #    msg = location
    #    return render_template('list.html', form=form, reagents=reagents, warning=msg)

    if request.method == 'GET':
        if id == 0:
            logs = Applog.query.all()
        else:
            logs = Applog.query.filter(Applog.product_id==id).all()

    if len(logs) > 0:
        flash("Log rows: " + str(len(logs)), 'info')
        return render_template('show_log.html', logs=logs)
    flash("No Logs Found!")
    return render_template('show_log.html')


#Handling error 404 and displaying relevant web page
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'),404

#Handling error 500 and displaying relevant web page
@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'),500

#Handling error 401 and displaying relevant web page
@app.errorhandler(401)
def not_auth_error(error):
    return render_template('401.html'),401
