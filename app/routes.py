from flask import render_template, make_response, flash, redirect, url_for, request, render_template_string
from app import app
from app import db
from app.forms import LoginForm, CreateForm, SearchForm
from app.models import Inventory, Locations, User, Role, UserRoles
from flask_user import current_user, login_required, roles_required, UserManager, UserMixin
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from datetime import datetime

user_manager = UserManager(app, db, User)
admin = Admin(app, name='reagentario', template_mode='bootstrap3')
from flask_admin.contrib.sqla.ajax import QueryAjaxModelLoader
from flask_admin.model import BaseModelView

class MyUserView(ModelView):
    form_ajax_refs = {
        'user': QueryAjaxModelLoader('user', db.session, User, fields=['roles'], page_size=10)
    }
    column_auto_select_related = True

  #  column_list = ('user', 'email')

admin.add_view(MyUserView(User, db.session))
admin.add_view(ModelView(Role, db.session))
admin.add_view(ModelView(UserRoles, db.session))
admin.add_view(ModelView(Inventory, db.session))
admin.add_view(ModelView(Locations, db.session))



with app.app_context():

    # Create 'member@example.com' user with no roles
    if not User.query.filter(User.email == 'member@example.com').first():
        user = User(
            email='member@example.com',
            email_confirmed_at=datetime.datetime.utcnow(),
            password=user_manager.hash_password('Password1'),
        )
        db.session.add(user)
        db.session.commit()

    # Create 'admin@example.com' user with 'Admin' and 'Agent' roles
    if not User.query.filter(User.email == 'admin@example.com').first():
        user = User(
            email='admin@example.com',
            email_confirmed_at=datetime.datetime.utcnow(),
            password=user_manager.hash_password('Password1'),
        )
        user.roles.append(Role(name='Admin'))
        user.roles.append(Role(name='Agent'))
        db.session.add(user)
        db.session.commit()


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for user {}, remember_me={}'.format(
            form.username.data, form.remember_me.data))
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)


# The Members page is only accessible to authenticated users
@app.route('/members')
@login_required    # Use of @login_required decorator
def member_page():
    return render_template_string("""
            {% extends "flask_user_layout.html" %}
            {% block content %}
                <h2>{%trans%}Members page{%endtrans%}</h2>
                <p><a href={{ url_for('user.register') }}>{%trans%}Register{%endtrans%}</a></p>
                <p><a href={{ url_for('user.login') }}>{%trans%}Sign in{%endtrans%}</a></p>
                <p><a href={{ url_for('index') }}>{%trans%}Home Page{%endtrans%}</a> (accessible to anyone)</p>
                <p><a href={{ url_for('member_page') }}>{%trans%}Member Page{%endtrans%}</a> (login_required: member@example.com / Password1)</p>
                <p><a href={{ url_for('user.logout') }}>{%trans%}Sign out{%endtrans%}</a></p>
            {% endblock %}
            """)

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
        flash("Number of reagents: " + str(len(reagents)))
        return render_template('list.html', form=form, reagents=reagents)
    else:
        flash("No Reagents Found!")
        msg = 'No Reagents Found'
        return render_template('list.html', form=form, warning=msg)


@app.route('/list_locations', methods=['GET'])
def list_locations():
    locations = Locations.query.all()

    if len(locations) > 0:
        flash(locations)
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
    return render_template('show.html', title=reagent.name, reagent=reagent)


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
            return make_response(
                f'{name} ({alias}) already created!'
            )
        db.session.add(location)
        db.session.commit()

        return redirect(url_for('list_locations'))
    return render_template('create_location.html')


@app.route('/create', methods=['GET', 'POST'])
def create():
    form = CreateForm(csrf_enabled=False)

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


