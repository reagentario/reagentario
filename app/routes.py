from flask import render_template, make_response, flash, redirect, url_for, request, render_template_string, Blueprint
from app import app
from app import db
from app.forms import LoginForm, CreateForm, SearchForm, EditForm
from app.models import Inventory, Locations, User, Products, ProdLoc, InventoryView
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.urls import url_parse

admin = Admin(app, name='reagentario', template_mode='bootstrap3')
from flask_admin.contrib.sqla.ajax import QueryAjaxModelLoader
from flask_admin.model import BaseModelView
from sqlalchemy import inspect

from flask_login import current_user, login_user, logout_user, login_required

admin.add_view(ModelView(User, db.session))
admin.add_view(InventoryView(Inventory, db.session))
admin.add_view(ModelView(Locations, db.session))
admin.add_view(ModelView(Products, db.session))
admin.add_view(ModelView(ProdLoc, db.session))


@app.route('/c')
def c():
    with app.app_context():

        # Create 'member@example.com' user with no roles
        if not User.query.filter(User.email == 'member@example.com').first():
            user = User(
                email='member@example.com',
                #email_confirmed_at=datetime.utcnow(),
                password=generate_password_hash('Password1'),
                alias='ME'
            )
            db.session.add(user)
            db.session.commit()

        # Create 'admin@example.com' user with 'Admin' and 'Agent' roles
        if not User.query.filter(User.email == 'admin2@example.com').first():
            user = User(
                email='admin2@example.com',
                #email_confirmed_at=datetime.utcnow(),
                password=generate_password_hash('Password1'),
                alias='A2'
            )
            if not user.check_password('Password1'):
                app.logger.debug("ERROR creating user admin")
                return render_template('index.html')
            app.logger.debug("created user admin")
            user.admin = True
            user.superadmin = True
            db.session.add(user)
            db.session.commit()

    return render_template('index.html')


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
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
        if not check_password_hash(existing_user.password, password):
            flash('Invalid password. Please try again.', 'danger')
            flash(existing_user.check_password(password), 'danger')
            return render_template('login.html', title='Sign In', form=form)
        login_user(existing_user, remember=form.remember_me.data)
        flash('You have successfully logged in.', 'success')
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    if form.errors:
        flash(form.errors, 'danger')
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    flash('You have successfully logged out.', 'success')
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, alias=form.alias.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/list', methods=['GET', 'POST'])
def list():
    form = SearchForm(csrf_enabled=False)

    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']  #Locations.query.get_or_404(form.location.data)
        reagents = Inventory.query.filter(db.and_(Inventory.name.like('%'+name+'%'), Inventory.location_id.like('%'+form.location.data+'%'))).all()
        msg = location
        return render_template('list.html', form=form, reagents=reagents, warning=msg)

    elif request.method == 'GET':
        reagents = Inventory.query.all()

    if len(reagents) > 0:
        flash("Number of reagents: " + str(len(reagents)), 'info')
        return render_template('list.html', form=form, reagents=reagents)
    else:
        flash("No Reagents Found!")
        msg = 'No Reagents Found'
        return render_template('list.html', form=form, warning=msg)


@app.route('/list_locations', methods=['GET'])
def list_locations():
    locations = Locations.query.all()

    if len(locations) > 0:
        return render_template('list_locations.html', locations=locations)
    else:
        flash("No Locations Found!")
        msg = 'No Locations Found'
        return render_template('list_locations.html', warning=msg)


@app.route('/list_location_content', methods=['GET', 'POST'])
def list_location_content(id):
    l = Locations.query.get_or_404(id)
    for r in l.reagents:
            print(f'> {r.name}')
    print('----')


@app.route('/show/<int:id>/')
def show(id):
    reagent = Inventory.query.get_or_404(id)
    app.logger.debug(reagent.name)
    app.logger.debug(type(reagent.location))
    app.logger.debug(type(reagent.amount))
    app.logger.debug(type(reagent.amount2))
    app.logger.debug(type(reagent.amount_limit))
    app.logger.debug(type(reagent.size))
    app.logger.debug(type(reagent.notes))
    app.logger.debug(type(reagent.to_be_ordered))

    return render_template('show.html', title=reagent.name, reagent=reagent)


@app.route('/edit/<int:id>/', methods=['GET', 'POST'])
def edit(id):
    #r = db.session.query(Inventory).filter(Inventory.id == id).with_for_update().first()
    r = db.session.query(Inventory).filter(Inventory.id == id).first()
    l = [(l.id, l.name) for l in Locations.query.all()]
    form = EditForm(csrf_enabled=False, exclude_fk=False, obj=r)

    #app.logger.debug("l = %s", l)
    form.location.choices = l
    #form.location.data = 2
    #form.location_id.choices = l
    #form.location_id.data = 2

    #form.name.data = r.name
    ##form.location.data = Locations.query.get_or_404(r.location_id)
    #form.amount.data = r.amount
    #form.amount2.data = r.amount2
    #form.size.data = r.size
    form.amount_limit.data = r.amount_limit
    #form.notes.data = r.notes
    #form.to_be_ordered.data = r.to_be_ordered

    if request.method == 'POST':
        app.logger.debug(form.name)
        app.logger.debug(form.location.data)
        app.logger.debug(type(form.location.data))
        app.logger.debug(type(form.amount.data))
        app.logger.debug(type(form.amount2.data))
        app.logger.debug(type(form.amount_limit.data))
        app.logger.debug(type(form.size.data))
        app.logger.debug(type(form.notes.data))
        app.logger.debug(type(form.to_be_ordered.data))



    if form.validate_on_submit():
        form.populate_obj(r)
        #save_changes(r, form)
        #name = request.form['name']
        #location = Locations.query.get_or_404(form.location.data)
        #app.logger.debug("loc: %s", form.location.data)
        #amount = request.form['amount']
        #amount2 = request.form['amount2']
        #size = request.form['size']
        #amount_limit = request.form['amount_limit']
        #notes = request.form['notes']
        #to_be_ordered = request.form['to_be_ordered']
        #reagent = Inventory(name=name,
        #                  location=location,
        #                  amount=amount,
        #                  amount2=amount2,
        #                  size=size,
        #                  amount_limit=amount_limit,
        #                  notes=notes,
        #                  to_be_ordered=to_be_ordered)
        try:
            app.logger.debug("updated id %s", r.id)
            db.session.commit()
        except Exception as e:
            flash('Error updating %s' % str(e), 'error')
            app.logger.debug("ERROR not updated id %s", r.id)
            db.session.rollback()
        #else:
        #    flash('Reagent updated', 'info')
        return redirect(url_for('show', id=id))

        return redirect(url_for('show', id=id))
    else:
         app.logger.debug("error on form validation")

#    elif not form.errors:
#        form.process(formdata=form.data, obj=r)

    return render_template('edit.html', id=id, form=form)


@app.route('/create_location', methods=['GET', 'POST'])
def create_location():
    if request.method == 'POST':
        name = request.form['name']
        alias = request.form['alias']
        location = Locations(name=name,
                          alias=alias)
        existing_location = Locations.query.filter(
            Locations.name == name or Locations.alias == alias
        ).first()
        if existing_location:
            # https://getbootstrap.com/docs/5.0/components/alerts/ colors
            flash('A Location with this name ({}) or alias ({}) already exists!'.format(name, alias), 'danger')
            return render_template('create_location.html')
        db.session.add(location)
        db.session.commit()
        return redirect(url_for('list_locations'))
    return render_template('create_location.html')


@app.route('/create', methods=['GET', 'POST'])
def create():
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

        return redirect(url_for('list'))

    return render_template('create.html', form=form)


@app.route('/locations')
def locations():
    locations = Locations.query.all()
    reagents = Inventory.query.all()
    res = {}
    for location in locations:
        res[location.id] = {
            'name': location.name
        }
    for reagent in locations.reagents:
        res[location.id]['reagents'] = {
            'id': reagent.id,
            'name': reagent.name
        }
    return jsonify(res)

@app.route('/plus/<int:id>/')
def plus(id):
    r = Inventory.query.get_or_404(id)
    r.amount += 1
    db.session.commit()
    return redirect(url_for('show', id = id))


@app.route('/minus/<int:id>/')
def minus(id):
    r = Inventory.query.get_or_404(id)
    if r.amount == 0:
        flash("No Reagents Found!")
        return redirect(url_for('show', id = id))
    else:
        r.amount -= 1
        db.session.commit()
        return redirect(url_for('show', id = id))


@app.route('/move/<int:id>/')
def move(id):
    r = Inventory.query.get_or_404(id)
    if r.amount2 == 0:
        flash("No more items available in the warehouse")
    else:
        r.amount2 -=1
        r.amount +=1
        db.session.commit()
        return redirect(url_for('show', id = id))


@app.route('/add/<int:id>/')
def add(id):
    r = Inventory.query.get_or_404(id)
    r.amount2 += 1
    db.session.commit()
    return redirect(url_for('show', id = id))
