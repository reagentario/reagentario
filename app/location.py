from flask import (
    render_template,
    make_response,
    flash,
    redirect,
    url_for,
    request,
    session,
)
from app import app
from app import db
from app import log
from app.forms import (
    CreateLocationForm,
    EditLocationForm,
)
from app.models import Inventory, Locations, Departments

from app.functions import add_log

from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError, PendingRollbackError

from flask_security import (
    current_user,
    auth_required,
    hash_password,
    login_required,
    roles_required,
    RoleMixin,
    UserMixin,
)

@app.route("/list_locations", methods=["GET"])
@auth_required()
def list_locations():
    """list all locations"""
    locations = Locations.query.all()

    if len(locations) > 0:
        return render_template(
            "list_locations.html", locations=locations, title="Locations"
        )
    flash("No Locations Found!")
    msg = "No Locations Found"
    return render_template("list_locations.html", warning=msg, title="Locations")


@app.route("/list_location_content/<int:_id>/", methods=["GET", "POST"])
@auth_required()
def list_location_content(_id):
    """list content of a location"""
    reagents = Inventory.query.filter(Inventory.location_id == _id).all()
    location = Locations.query.filter(Locations.id == _id).first()
    loc_name = location.name

    if len(reagents) > 0:
        return render_template("list.html", title=loc_name, reagents=reagents)
    flash("No Reagents Found!")
    msg = "No Reagents Found in this location"
    return render_template("list.html", title=loc_name, warning=msg)


@app.route("/create_location", methods=["GET", "POST"])
@auth_required()
@roles_required("admin")
def create_location():
    """create a new location form"""

    form = CreateLocationForm(csrf_enabled=False)

    if request.method == "POST":
        name = request.form["name"]
        short_name = request.form["short_name"]
        department = Departments.query.get_or_404(form.department.data)

        if not current_user.has_role(department.short_name):
            flash(
                f"You have not permission to create a location for {department}",
                "danger",
            )
            return render_template("create_location.html", form=form, title="Add a new location")

        existing_location = Locations.query.filter(
            Locations.name == name or Locations.short_name == short_name
        ).first()
        if existing_location:
            # https://getbootstrap.com/docs/5.0/components/alerts/ colors
            flash(
                f"A Location with this name ({name}) or short_name ({short_name}) already exists!",
                "danger",
            )
            return render_template("create_location.html", form=form, title="Add a new location")

        location = Locations(
            name=name,
            short_name=short_name,
            department=department,
        )
        db.session.add(location)
        db.session.commit()
        db.session.refresh(location)
        log.debug(f"created location id {location.id} (name: {location.name}) by user id {current_user.id} (email: {current_user.email})")

        return redirect(url_for("list_locations"))
    return render_template("create_location.html", form=form, title="Add a new location")


@app.route("/delete_location/<int:_id>/", methods=["GET"])
@auth_required()
@roles_required("admin")
def delete_location(_id):
    """delete a location"""

    location = db.session.query(Locations).filter(Locations.id == _id).first()

    if location:

        if not current_user.has_role(location.department.short_name):
            flash(
                f"You have not permission to delete a location for {location.department.name}",
                "danger",
            )
            return redirect(url_for("list_locations"))

        reagents_in = Inventory.query.filter(Inventory.location_id == _id).all()
        if len(reagents_in) > 0:
            flash(
                f"Location {location.name} contains some reagents, it cannot be deleted",
                "danger",
            )
            return redirect(url_for("list_locations"))
        try:
            db.session.delete(location)
            db.session.commit()
            add_log(
                location.id,
                current_user.id,
                f"deleted location {location.id} - {location.name}",
            )
            flash(f"Location {location.name} deleted", "info")
            log.debug(f"deleted location id {location.id} (name: {location.name}) by user id {current_user.id} (email: {current_user.email})")
        except Exception as e:
            flash(f"Error deleting location {location.name} with error {str(e)}", "danger")
            db.session.rollback()
    else:
        flash(f"Error deleting location with id {str(location.id)}", "danger")
        return redirect(url_for("list_locations"))
    return redirect(url_for("list_locations"))


@app.route("/edit_location/<int:_id>/", methods=["GET", "POST"])
@auth_required()
@roles_required("admin")
def edit_location(_id):
    """edit location form"""
    try:
        loc = db.session.query(Locations).filter(Locations.id == _id).first()
        if not loc:
            flash("Not existing location", "danger")
            return redirect(url_for("list_locations"))

        if not current_user.has_role(loc.department.short_name):
            flash(
                f"You have not permission to edit a location for {loc.department.name}",
                "danger",
            )
            return redirect(url_for("list_locations"))

        dept = [(dept.id, dept.name) for dept in Departments.query.all()]
        form = EditLocationForm(csrf_enabled=False, exclude_fk=False, obj=loc)
        form.department.choices = dept
        form.department.data = loc.department.id
        l1 = loc.__dict__.copy()

        if form.validate_on_submit():
            existing_location = (
                db.session.query(Locations)
                .filter(
                    Locations.name == form.name.data
                    or Locations.short_name == form.short_name.data
                )
                .filter(Locations.id != _id)
                .first()
            )
            if existing_location:
                flash(
                    f"A Location with this name ({form.name.data}) or short_name ({form.short_name.data}) already exists!",
                    "danger",
                )
                return render_template(
                    "edit_location.html", title="Edit Location", _id=_id, form=form
                )

            dept_selected = request.form["department"]
            loc.name = request.form["name"]
            loc.short_name = request.form["short_name"]
            loc.department = Departments.query.get(dept_selected)

            l2 = loc.__dict__.copy()
            k1 = set(l1.keys())
            k2 = set(l2.keys())
            common_keys = set(k1).intersection(set(k2))
            try:
                db.session.commit()
                flash("Your changes have been saved.")

                for key in common_keys:
                    if str(l1[key]) != str(l2[key]):
                        log.debug(
                            loc.id,
                            current_user.id,
                            f'updated item {loc.id} - {loc.name}: {key} value changed from "{str(l1[key])}" to "{str(l2[key])}" by user {current_user.email}',
                        )
            except Exception as e:
                flash(f"Error updating location id {str(loc.id)} with error {str(e)}", "danger")
                db.session.rollback()
                return render_template(
                    "edit_location.html", title="Edit Location", _id=_id, form=form
                )

            return redirect(url_for("list_locations"))

        return render_template("edit_location.html", _id=_id, form=form, title="Edit location")

    except Exception as e:
        flash(f"Error updating location id {str(loc.id)} with error {str(e)}", "danger")
        db.session.rollback()
        return render_template(
            "edit_location.html", title="Edit Location", _id=_id, form=form
        )
