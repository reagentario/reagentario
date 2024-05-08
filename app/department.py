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
    EditDepartmentForm,
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


@app.route("/list_departments", methods=["GET"])
@auth_required()
def list_departments():
    """list all departments"""
    departments = Departments.query.all()

    if len(departments) > 0:
        return render_template(
            "list_departments.html", departments=departments, title="Departments"
        )
    flash("No Departments Found!")
    msg = "No Departments Found"
    return render_template("list_departments.html", warning=msg, title="Departments")


@app.route("/create_department", methods=["GET", "POST"])
@auth_required()
@roles_required("superadmin")
def create_department():
    """create a new department form"""

    if request.method == "POST":
        name = request.form["name"]
        short_name = request.form["short_name"]
        department = Departments(name=name, short_name=short_name)
        existing_department = Departments.query.filter(
            Departments.name == name or Departments.short_name == short_name
        ).first()
        if existing_department:
            # https://getbootstrap.com/docs/5.0/components/alerts/ colors
            flash(
                f"A Department with this name ({name}) or short_name ({short_name}) already exists!",
                "danger",
            )
            return render_template(
                "create_department.html", title="Add a new department"
            )
        db.session.add(department)
        db.session.commit()
        log.debug(
            f"created department {department.id} - {department.name} by user {current_user.id}"
        )

        return redirect(url_for("list_departments"))
    return render_template("create_department.html", title="Add a new department")


@app.route("/delete_department/<int:_id>/", methods=["GET"])
@auth_required()
@roles_required("superadmin")
def delete_department(_id):
    """delete a department"""

    department = db.session.query(Departments).filter(Departments.id == _id).first()
    if department:
        locations_in = Locations.query.filter(Locations.department_id == _id).all()
        if len(locations_in) > 0:
            flash(
                f"There are locations pertaining to {department.name} department, it cannot be deleted",
                "danger",
            )
            return redirect(url_for("list_departments"))
        try:
            db.session.delete(department)
            db.session.commit()
            add_log(
                department.id,
                current_user.id,
                f"deleted department {department.id} - {department.name}",
            )
            flash("Department deleted", "info")
            log.debug(
                f"deleted department id {department.id} by user {current_user.id}"
            )
        except Exception as e:
            flash(f"Error deleting {department.id} with error {str(e)}", "danger")
            db.session.rollback()
    else:
        flash(f"Error deleting department with id {str(department.id)}", "danger")
        return redirect(url_for("list_departments"))
    return redirect(url_for("list_departments"))


@app.route("/edit_department/<int:_id>/", methods=["GET", "POST"])
@auth_required()
@roles_required("superadmin")
def edit_department(_id):
    """edit department form"""

    form = EditDepartmentForm()
    department = db.session.query(Departments).filter(Departments.id == _id).first()
    if not department:
        flash("Not existing department", "danger")
        return redirect(url_for("list_departments"))

    try:
        if form.validate_on_submit():
            existing_department = (
                db.session.query(Departments)
                .filter(
                    Departments.name == form.name.data
                    or Departments.short_name == form.short_name.data
                )
                .filter(Departments.id != _id)
                .first()
            )
            if existing_department:
                flash(
                    f"A Department with this name ({form.name.data}) or short_name ({form.short_name.data}) already exists!",
                    "danger",
                )
                return render_template(
                    "edit_department.html", title="Edit Department", _id=_id, form=form
                )
            try:
                department.name = form.name.data
                department.short_name = form.short_name.data
                db.session.commit()
                flash("Your changes have been saved.")
                log.debug(
                    f"Department {department.id} updated by user {current_user.id}: name={department.name}, short_name={department.short_name}"
                )
                return redirect(url_for("list_departments"))
            except Exception as e:
                flash(f"Error editing {department.id} with error {str(e)}", "danger")
                db.session.rollback()
                return render_template(
                    "edit_department.html", title="Edit Department", _id=_id, form=form
                )
    except IntegrityError:
        flash(f"Error editing {department.id}", "danger")
        db.session.rollback()
        return render_template(
            "edit_department.html", title="Edit Department", _id=_id, form=form
        )
    except PendingRollbackError as e:
        flash(f"Error editing {department.id} with error {str(e)}", "danger")
        db.session.rollback()
        return render_template(
            "edit_department.html", title="Edit Department", _id=_id, form=form
        )

    if request.method == "GET":
        form.name.data = department.name
        form.short_name.data = department.short_name
        return render_template(
            "edit_department.html", title="Edit Department", _id=_id, form=form
        )
    return redirect(url_for("list_departments"))
