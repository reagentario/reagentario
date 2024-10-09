from datetime import (
    datetime,
    date,
    timedelta,
)

from dateutil.relativedelta import relativedelta

from flask import (
    render_template,
    make_response,
    flash,
    redirect,
    url_for,
    request,
    session,
    send_file,
)
from app import app
from app import db
# from app import log
from app.forms import (
    CreateCalibrationForm,
    EditCalibrationForm,
)
from app.models import Calibrations, Departments, CalibrationsLog
from app.functions import add_calibration_log, calculate_next_calibration_date

from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError, PendingRollbackError

from flask_security import (
    current_user,
    auth_required,
    login_required,
    roles_required,
    RoleMixin,
    UserMixin,
)


@app.route("/list_calibrations", methods=["GET", "POST"])
@auth_required()
@login_required
def list_calibrations():
    """list all calibrations"""

    if request.method == "GET":
        calibrations = Calibrations.query.all()

    if len(calibrations) > 0:
        return render_template(
            "list_calibrations.html", calibrations=calibrations, title="Calibrations"
        )
    msg = "No Calibrations Found"
    return render_template("list_calibrations.html", warning=msg, title="Calibrations")


@app.route("/list_calibrations_next_month", methods=["GET", "POST"])
@auth_required()
@login_required
def list_calibrations_next_month():
    """list calibrations expiring next month"""

    next_month = datetime.now().month + 1
    month = date.today().replace(month=next_month).strftime("%B-%Y")

    if request.method == "GET":
        from_date = date(
            year=datetime.now().year, month=(datetime.now().month + 1), day=1
        )

        # move to first next month
        nm = date.today().replace(day=28) + timedelta(days=4)
        # Now move to the second next month
        nm = nm.replace(day=28) + timedelta(days=4)
        # come back to the first next month's last day
        to_date = nm - timedelta(days=nm.day)
        calibrations = (
            Calibrations.query.filter(Calibrations.next_calibration_date >= from_date)
            .filter(Calibrations.next_calibration_date <= to_date)
            .all()
        )

    title = f"Calibrations {month}"

    if len(calibrations) > 0:
        return render_template(
            "list_calibrations.html", calibrations=calibrations, title=title
        )
    msg = "No Calibrations Found"
    return render_template("list_calibrations.html", warning=msg, title=title)


@app.route("/list_calibrations_this_month", methods=["GET", "POST"])
@auth_required()
@login_required
def list_calibrations_this_month():
    """list calibrations expiring this month"""

    month = date.today().strftime("%B-%Y")

    if request.method == "GET":
        from_date = date(year=datetime.now().year, month=(datetime.now().month), day=1)

        # move to first next month
        nm = date.today().replace(day=28) + timedelta(days=4)
        # come back to this month's last day
        to_date = nm - timedelta(days=nm.day)
        calibrations = (
            Calibrations.query.filter(Calibrations.next_calibration_date >= from_date)
            .filter(Calibrations.next_calibration_date <= to_date)
            .all()
        )

    title = f"Calibrations {month}"

    if len(calibrations) > 0:
        return render_template(
            "list_calibrations.html", calibrations=calibrations, title=title
        )
    msg = "No Calibrations Found"
    return render_template("list_calibrations.html", warning=msg, title=title)


@app.route("/show_calibration/<int:_id>/")
@auth_required()
def show_calibration(_id):
    """show a specific calibration"""
    calibration = Calibrations.query.get_or_404(_id)
    return render_template(
        "show_calibration.html", title=calibration.name, calibration=calibration
    )


@app.route("/create_calibration", methods=["GET", "POST"])
@auth_required()
@roles_required("admin")
def create_calibration():
    """create a new calibration form"""

    title = "Add a new Calibration"
    form = CreateCalibrationForm(csrf_enabled=False)
    form.description = ""
    form.apparatus = ""
    form.frequency.data = 0
    form.tolerance.data = 0
    form.notes = ""
    form.initial_check_date.data = date.today()
    form.last_calibration_date.data = date.today()

    if request.method == "POST":
        name = request.form["name"]
        apparatus = request.form["apparatus"]
        description = request.form["description"]
        department = Departments.query.get_or_404(form.department.data)
        initial_check_date = request.form["initial_check_date"]
        frequency = request.form["frequency"]
        frequency_units = request.form["frequency_units"]
        tolerance = request.form["tolerance"]
        tolerance_units = request.form["tolerance_units"]
        last_calibration_date = request.form["last_calibration_date"]
        notes = request.form["notes"]
        # calculate a next calibration time
        init = datetime.strptime(initial_check_date, "%Y-%m-%d").date()
        if frequency_units == "days":
            nextc = init + relativedelta(days=+int(frequency))
        elif frequency_units == "weeks":
            nextc = init + relativedelta(weeks=+int(frequency))
        elif frequency_units == "months":
            nextc = init + relativedelta(months=+int(frequency))
        elif frequency_units == "years":
            nextc = init + relativedelta(years=+int(frequency))
        else:
            nextc = init

        calibration = Calibrations(
            name=name,
            apparatus=apparatus,
            description=description,
            department=department,
            initial_check_date=initial_check_date,
            frequency=frequency,
            frequency_units=frequency_units,
            tolerance=tolerance,
            tolerance_units=tolerance_units,
            last_calibration_date=last_calibration_date,
            next_calibration_date=nextc,
            notes=notes,
        )

        if not current_user.has_role(department.short_name):
            flash(
                f"You have not permission to add a calibration in a location pertaining to {department.name}",
                "danger",
            )
            return redirect(url_for("create_calibration"))

        db.session.add(calibration)
        db.session.commit()
        db.session.refresh(calibration)
        add_calibration_log(
            calibration.id,
            current_user.id,
            f"created calibration {calibration.id} - {calibration.name}",
        )
        return redirect(url_for("list_calibrations"))

    return render_template("create_calibration.html", form=form, title=title)


@app.route("/edit_calibration/<int:_id>/", methods=["GET", "POST"])
@auth_required()
@roles_required("admin")
def edit_calibration(_id):
    """edit a specific calibration"""
    calib = db.session.query(Calibrations).filter(Calibrations.id == _id).first_or_404()

    dep = [(dep.id, dep.name) for dep in Departments.query.all()]
    form = EditCalibrationForm(csrf_enabled=False, exclude_fk=False, obj=calib)
    form.department.choices = dep
    form.department.data = calib.department.id

    if not current_user.has_role(calib.department.short_name):
        flash(
            f"You have not permission to edit a calibration pertaining to {calib.department.name}",
            "danger",
        )
        return redirect(url_for("show_calibration", _id=_id))

    r1 = calib.__dict__.copy()

    if form.validate_on_submit():
        dep_selected = request.form["department"]
        calib.name = request.form["name"]
        calib.apparatus = request.form["apparatus"]
        calib.description = request.form["description"]
        calib.department = Departments.query.get(dep_selected)
        calib.initial_check_date = request.form["initial_check_date"]
        calib.frequency = request.form["frequency"]
        calib.frequency_units = request.form["frequency_units"]
        calib.tolerance = request.form["tolerance"]
        calib.tolerance_units = request.form["tolerance_units"]
        calib.last_calibration_date = request.form["last_calibration_date"]
        calib.next_calibration_date = calculate_next_calibration_date(calib.id)
        calib.notes = request.form["notes"]
        r2 = calib.__dict__.copy()
        k1 = set(r1.keys())
        k2 = set(r2.keys())
        common_keys = set(k1).intersection(set(k2))
        try:
            db.session.commit()
            for key in common_keys:
                if str(r1[key]) != str(r2[key]):
                    add_calibration_log(
                        calib.id,
                        current_user.id,
                        f'updated calibration {calib.id} - {calib.name}: {key} value changed from "{str(r1[key])}" to "{str(r2[key])}"',
                    )
        except Exception as e:
            flash(f"Error updating {str(e)}", "danger")
            db.session.rollback()
        return redirect(url_for("show_calibration", _id=_id))

    return render_template(
        "edit_calibration.html", _id=_id, form=form, title="Edit calibration"
    )


@app.route("/delete_calibration/<int:_id>/", methods=["GET"])
@auth_required()
@roles_required("admin")
def delete_calibration(_id):
    """delete a specific calibration"""

    calibration = db.session.query(Calibrations).filter(Calibrations.id == _id).first()
    if calibration:
        if not current_user.has_role(calibration.department.short_name):
            flash(
                f"You have not permission to delete a calibration pertaining to {calibration.department.name}",
                "danger",
            )
            return redirect(url_for("show_calibration", _id=_id))

        try:
            db.session.delete(calibration)
            db.session.commit()
            add_calibration_log(
                calibration.id,
                current_user.id,
                f"deleted calibration {calibration.id} - {calibration.name}",
            )
            flash("Calibration deleted", "info")
        except Exception as e:
            flash(f"Error deleting {calibration.id} with error {str(e)}", "danger")
            db.session.rollback()
    else:
        flash(f"Error deleting calibration with id {_id}", "danger")
        return redirect(url_for("show_calibration", _id=_id))
    return redirect(url_for("list_calibrations"))


@app.route("/show_calibration_log/<int:_id>/")
@auth_required()
@roles_required("admin")
def show_calibration_log(_id):
    """list logs"""

    if request.method == "GET":
        if _id == 0:
            logs = CalibrationsLog.query.all()
        else:
            logs = CalibrationsLog.query.filter(
                CalibrationsLog.calibration_id == _id
            ).all()

    if len(logs) > 0:
        flash(f"Log rows: {str(len(logs))}", "info")
        return render_template(
            "show_calibration_log.html", logs=logs, title="Calibration Logs report"
        )
    flash("No Logs Found for this calibration !", "info")
    return render_template("show_calibration_log.html", title="Calibration Logs report")


@app.route("/set_calibration_date/<int:_id>/")
@auth_required()
@roles_required("admin")
def set_calibration_date(_id):
    """Set last and calculate next calibration date"""
    calib = db.session.query(Calibrations).filter(Calibrations.id == _id).first()

    if calib:
        if not current_user.has_role(calib.department.short_name):
            flash(
                f"You have not permission to set calibration date for something pertaining to {calib.department.name}",
                "danger",
            )
            return redirect(url_for("show_calibration", _id=_id))

        calib.last_calibration_date = date.today()

        try:
            db.session.commit()
        except Exception as e:
            flash(
                f"Error setting last calibration date for {calib.id} - {calib.name} with error {str(e)}",
                "danger",
            )

            db.session.rollback()

        calib.next_calibration_date = calculate_next_calibration_date(_id)

        try:
            db.session.commit()
            flash(
                f"Set calibration date for {calib.name} - {calib.description}   (last: {calib.last_calibration_date}, next: {calib.next_calibration_date})",
                "info",
            )
            add_calibration_log(
                calib.id,
                current_user.id,
                f"Set calibration date for {calib.id} - {calib.name} - {calib.description} - {calib.last_calibration_date}",
            )
        except Exception as e:
            flash(
                f"Error setting next calibration date for {calib.id} - {calib.name} with error {str(e)}",
                "danger",
            )
            db.session.rollback()
    else:
        flash(f"Error setting calibration for id {str(_id)}", "danger")
        return redirect(url_for("show_calibration", _id=_id))
    return redirect(url_for("show_calibration", _id=_id, title=calib.name))


@app.route("/show_cal_log/<int:_id>/")
@auth_required()
@roles_required("admin")
def show_cal_log(_id):
    """list calibration logs"""

    if request.method == "GET":
        if _id == 0:
            logs = CalibrationsLog.query.all()
        else:
            logs = CalibrationsLog.query.filter(CalibrationsLog.calibration_id == _id).all()

    if len(logs) > 0:
        flash(f"Log rows: {str(len(logs))}", "info")
        return render_template("show_cal_log.html", logs=logs, title="Calibration Logs report")
    flash("No Logs Found for this calibration !", "info")
    return render_template("show_cal_log.html", title="Calibration Logs report")


@app.template_filter("datedelta")
def datedelta(next_cal, tolerance, unit):
    color = ''
    today = date.today()
    # Define the time delta based on the unit
    if unit == "days":
        delta = relativedelta(days=tolerance)
    elif unit == "weeks":
        delta = relativedelta(weeks=tolerance)
    elif unit == "months":
        delta = relativedelta(months=tolerance)
    else:
        raise ValueError("Invalid unit. Must be 'days', 'weeks', or 'months'.")

    # last date that will have a color assigned
    future_threshold = today + relativedelta(days=30)
    tolerance_threshold = today + delta
    expiry_threshold = today - delta

    if next_cal < future_threshold:
        color = "lightgreen"
    if next_cal < tolerance_threshold:
        color = "orange"
    if next_cal < expiry_threshold:
        color = "red"
    if not color:
        color = "white"
    return color
