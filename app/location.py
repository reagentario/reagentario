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
    EditLocationForm,
)
from app.models import Inventory, Locations

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
        flash(f"Number of reagents: {str(len(reagents))}", "info")
        return render_template("list.html", title=loc_name, reagents=reagents)
    flash("No Reagents Found!")
    msg = "No Reagents Found in this location"
    return render_template("list.html", title=loc_name, warning=msg)


@app.route("/create_location", methods=["GET", "POST"])
@auth_required()
@roles_required("admin")
def create_location():
    """create a new location form"""

    if request.method == "POST":
        name = request.form["name"]
        short_name = request.form["short_name"]
        location = Locations(name=name, short_name=short_name)
        existing_location = Locations.query.filter(
            Locations.name == name or Locations.short_name == short_name
        ).first()
        if existing_location:
            # https://getbootstrap.com/docs/5.0/components/alerts/ colors
            flash(
                f"A Location with this name ({name}) or short_name ({short_name}) already exists!",
                "danger",
            )
            return render_template("create_location.html", title="Add a new location")
        db.session.add(location)
        db.session.commit()
        log.debug(f"created location {location.id} - {location.name} by user {current_user.id}")

        return redirect(url_for("list_locations"))
    return render_template("create_location.html", title="Add a new location")


@app.route("/delete_location/<int:_id>/", methods=["GET"])
@auth_required()
@roles_required("admin")
def delete_location(_id):
    """delete a location"""

    location = db.session.query(Locations).filter(Locations.id == _id).first()
    if location:
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
            flash("Location deleted", "info")
            log.debug(f"deleted location id {location.id} by user {current_user.id}")
        except Exception as e:
            flash(f"Error deleting {location.id} with error {str(e)}", "danger")
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

    form = EditLocationForm()
    location = db.session.query(Locations).filter(Locations.id == _id).first()
    if not location:
        flash("Not existing location", "danger")
        return redirect(url_for("list_locations"))

    try:
        if form.validate_on_submit():
            # existing_location = Locations.query.filter(Locations.name == form.name.data or Locations.short_name == form.short_name.data).first()
            existing_location = (
                db.session.query(Locations)
                .filter(
                    Locations.name == form.name.data
                    or Locations.short_name == form.short_name.data
                )
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
            try:
                location.name = form.name.data
                location.short_name = form.short_name.data
                db.session.commit()
                flash("Your changes have been saved.")
                log.debug(
                    f"Location {location.id} updated by user {current_user.id}: name={location.name}, short_name={location.short_name}"
                )
                return redirect(url_for("list_locations"))
            except Exception as e:
                flash(f"Error editing {location.id} with error {str(e)}", "danger")
                db.session.rollback()
                return render_template(
                    "edit_location.html", title="Edit Location", _id=_id, form=form
                )
    except IntegrityError:
        flash(f"Error editing {location.id}", "danger")
        db.session.rollback()
        return render_template(
            "edit_location.html", title="Edit Location", _id=_id, form=form
        )
    except PendingRollbackError as e:
        flash(f"Error editing {location.id} with error {str(e)}", "danger")
        db.session.rollback()
        return render_template(
            "edit_location.html", title="Edit Location", _id=_id, form=form
        )

    if request.method == "GET":
        form.name.data = location.name
        form.short_name.data = location.short_name
        return render_template(
            "edit_location.html", title="Edit Location", _id=_id, form=form
        )
    return redirect(url_for("list_locations"))
