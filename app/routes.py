from flask import render_template, make_response, flash, redirect, url_for, request
from app import app
from app import db
from app.forms import LoginForm, CreateForm, SearchForm
from app.models import Inventory, Locations

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
        reagent = Inventory(name=name,
                          location=location)
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
