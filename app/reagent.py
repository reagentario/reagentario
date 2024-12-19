import csv
import os

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
from app import log
from app.forms import (
    CreateForm,
    SearchForm,
    EditForm,
)
from app.models import Inventory, Locations, Applog
from app.functions import add_log

from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError, PendingRollbackError

from flask_security import (
    current_user,
    auth_required,
    roles_required,
    RoleMixin,
    UserMixin,
)

from datetime import (
    datetime,
    timedelta,
)

@app.route("/list", methods=["GET", "POST"])
@auth_required()
def list():
    """list all reagents"""
    form = SearchForm(csrf_enabled=False)

    if request.method == "POST":
        name = request.form["name"]
        location = request.form[
            "location"
        ]  # Locations.query.get_or_404(form.location.data)
        reagents = Inventory.query.filter(
            db.and_(
                Inventory.name.like("%" + name + "%"),
                Inventory.location_id.like("%" + form.location.data + "%"),
            )
        ).all()
        msg = location
        return render_template("list.html", form=form, reagents=reagents, warning=msg)

    if request.method == "GET":
        reagents = Inventory.query.all()

    if len(reagents) > 0:
        return render_template("list.html", form=form, reagents=reagents)
    flash("No Reagents Found!")
    msg = "No Reagents Found"
    return render_template("list.html", form=form, warning=msg)


@app.route("/show/<int:_id>/")
@auth_required()
def show(_id):
    """show a specific reagent"""
    reagent = Inventory.query.get_or_404(_id)
    return render_template("show.html", title=reagent.name, reagent=reagent)


@app.route("/create", methods=["GET", "POST"])
@auth_required()
@roles_required("admin")
def create():
    """create a new reagent form"""

    title = "Add a new Reagent"
    form = CreateForm(csrf_enabled=False)
    form.amount.data = 0
    form.amount2.data = 0
    form.amount_limit.data = 0
    form.order.data = 0

    if request.method == "POST":
        name = request.form["name"]
        location = Locations.query.get_or_404(form.location.data)
        amount = request.form["amount"]
        amount2 = request.form["amount2"]
        size = request.form["size"]
        amount_limit = request.form["amount_limit"]
        cas_number = request.form["cas_number"]
        product_code = request.form["product_code"]
        supplier = request.form["supplier"]
        batch = request.form["batch"]
        expiry_date = request.form["expiry_date"]
        notes = request.form["notes"]
        order = request.form["order"]
        reagent = Inventory(
            name=name,
            location=location,
            amount=amount,
            amount2=amount2,
            size=size,
            amount_limit=amount_limit,
            cas_number=cas_number,
            product_code=product_code,
            supplier=supplier,
            batch=batch,
            expiry_date=expiry_date,
            notes=notes,
            order=order,
        )

        if not current_user.has_role(location.department.short_name):
            flash(
                f"You have not permission to add a reagent in a location pertaining to {location.department.name}",
                "danger",
            )
            return redirect(url_for("create"))

        db.session.add(reagent)
        db.session.commit()
        db.session.refresh(reagent)
        add_log(
            reagent.id,
            current_user.id,
            f"created item {reagent.id} - {reagent.name}"
        )
        return redirect(url_for("list"))

    return render_template("create.html", form=form, title=title)


@app.route("/edit/<int:_id>/", methods=["GET", "POST"])
@auth_required()
@roles_required("admin")
def edit(_id):
    """edit a specific reagent"""
    reag = db.session.query(Inventory).filter(Inventory.id == _id).first_or_404()
    loc = [(loc.id, loc.name) for loc in Locations.query.all()]
    form = EditForm(csrf_enabled=False, exclude_fk=False, obj=reag)
    form.location.choices = loc
    form.location.data = reag.location.id

    if not current_user.has_role(reag.location.department.short_name):
        flash(
            f"You have not permission to edit a reagent in a location pertaining to {reag.location.department.name}",
            "danger",
        )
        return redirect(url_for("show", _id=_id))

    r1 = reag.__dict__.copy()

    if form.validate_on_submit():
        loc_selected = request.form["location"]
        reag.name = request.form["name"]
        reag.location = Locations.query.get(loc_selected)
        reag.amount = request.form["amount"]
        reag.amount2 = request.form["amount2"]
        reag.size = request.form["size"]
        reag.amount_limit = request.form["amount_limit"]
        reag.cas_number = request.form["cas_number"]
        reag.product_code = request.form["product_code"]
        reag.supplier = request.form["supplier"]
        reag.batch = request.form["batch"]
        reag.expiry_date = request.form["expiry_date"]
        reag.notes = request.form["notes"]
        reag.order = request.form["order"]
        r2 = reag.__dict__.copy()
        k1 = set(r1.keys())
        k2 = set(r2.keys())
        common_keys = set(k1).intersection(set(k2))
        try:
            db.session.commit()
            for key in common_keys:
                if str(r1[key]) != str(r2[key]):
                    add_log(
                        reag.id,
                        current_user.id,
                        f'updated item {reag.id} - {reag.name}: {key} value changed from "{str(r1[key])}" to "{str(r2[key])}"',
                    )
        except Exception as e:
            flash(f"Error updating {str(e)}", "danger")
            db.session.rollback()
        return redirect(url_for("show", _id=_id))

    return render_template("edit.html", _id=_id, form=form, title="Edit reagent")


@app.route("/delete/<int:_id>/", methods=["GET"])
@auth_required()
@roles_required("admin")
def delete(_id):
    """delete a specific reagent"""

    reagent = db.session.query(Inventory).filter(Inventory.id == _id).first()
    if reagent:
        if not current_user.has_role(reagent.location.department.short_name):
            flash(
                f"You have not permission to delete a reagent in a location pertaining to {reagent.location.department.name}",
                "danger",
            )
            return redirect(url_for("show", _id=_id))

        try:
            db.session.delete(reagent)
            db.session.commit()
            add_log(
                reagent.id,
                current_user.id,
                f"deleted item {reagent.id} - {reagent.name}",
            )
            flash("Item deleted", "info")
        except Exception as e:
            flash(f"Error deleting {reagent.id} with error {str(e)}", "danger")
            db.session.rollback()
    else:
        flash(f"Error deleting product with id {_id}", "danger")
        return redirect(url_for("show", _id=_id))
    return redirect(url_for("list"))


@app.route("/plus/<int:_id>/")
@auth_required()
@roles_required("admin")
def plus(_id):
    """add 1 item of a specific reagent in lab"""
    reagent = Inventory.query.get_or_404(_id)

    if not current_user.has_role(reagent.location.department.short_name):
        flash(
            f"You have not permission to add a reagent in a location pertaining to {reagent.location.department.name}",
            "danger",
        )
        return redirect(url_for("show", _id=_id))


    reagent.amount += 1
    db.session.commit()
    # flash("Added 1 item to laboratory", "info")
    add_log(reagent.id, current_user.id, f"added itemid {reagent.id} - {reagent.name}")
    return redirect(url_for("show", _id=_id))


@app.route("/minus/<int:_id>/")
@auth_required()
@roles_required("admin")
def minus(_id):
    """remove 1 item of a specific reagent in lab"""
    reagent = Inventory.query.get_or_404(_id)

    if not current_user.has_role(reagent.location.department.short_name):
        flash(
            f"You have not permission to remove a reagent in a location pertaining to {reagent.location.department.name}",
            "danger",
        )
        return redirect(url_for("show", _id=_id))

    if reagent.amount == 0:
        flash("No more items available in laboratory!", "danger")
        return redirect(url_for("show", _id=_id))
    reagent.amount -= 1
    db.session.commit()
    # flash("Removed 1 item from laboratory", "info")
    add_log(reagent.id, current_user.id, f"removed itemid {reagent.id} - {reagent.name}")

    return redirect(url_for("show", _id=_id))


@app.route("/move/<int:_id>/")
@auth_required()
@roles_required("admin")
def move(_id):
    """move 1 item of a specific reagent from warehouse to lab"""
    reagent = Inventory.query.get_or_404(_id)

    if not current_user.has_role(reagent.location.department.short_name):
        flash(
            f"You have not permission to move a reagent in a location pertaining to {reagent.location.department.name}",
            "danger",
        )
        return redirect(url_for("show", _id=_id))

    if reagent.amount2 == 0:
        flash("No more items available in the warehouse", "danger")
        return redirect(url_for("show", _id=_id))

    reagent.amount2 -= 1
    reagent.amount += 1
    db.session.commit()
    # flash("Moved one item from warehouse to laboratory", "info")
    add_log(
        reagent.id,
        current_user.id,
        f"moved from warehouse itemid {reagent.id} - {reagent.name}",
    )
    return redirect(url_for("show", _id=_id))


@app.route("/add/<int:_id>/")
@auth_required()
@roles_required("admin")
def add(_id):
    """add 1 item of a specific reagent to warehouse"""
    reagent = Inventory.query.get_or_404(_id)

    if not current_user.has_role(reagent.location.department.short_name):
        flash(
            f"You have not permission to add a reagent in a location pertaining to {reagent.location.department.name}",
            "danger",
        )
        return redirect(url_for("show", _id=_id))

    reagent.amount2 += 1
    db.session.commit()
    # flash("Added 1 item to warehouse", "info")
    add_log(
        reagent.id,
        current_user.id,
        f"added to warehouse itemid {reagent.id} - {reagent.name}",
    )
    return redirect(url_for("show", _id=_id))


@app.route("/show_log/<int:_id>/")
@auth_required()
@roles_required("admin")
def show_log(_id):
    """list logs"""

    if request.method == "GET":
        if _id == 0:
            logs = Applog.query.all()
        else:
            logs = Applog.query.filter(Applog.product_id == _id).all()

    if len(logs) > 0:
        flash(f"Log rows: {str(len(logs))}", "info")
        return render_template("show_log.html", logs=logs, title="Logs report")
    flash("No Logs Found for this reagent !", "info")
    return render_template("show_log.html", title="Logs report")


@app.route("/order/<int:_id>/", methods=["GET"])
@auth_required()
def order(_id):
    """set order for a reagent"""
    reagent = db.session.query(Inventory).filter(Inventory.id == _id).first()
    if reagent:
        if not current_user.has_role(reagent.location.department.short_name):
            flash(
                f"You have not permission to order a reagent in a location pertaining to {reagent.location.department.name}",
                "danger",
            )
            return redirect(url_for("show", _id=_id))

        reagent.order += 1
        try:
            db.session.commit()
            flash(f"Set order for 1 unit of item {reagent.name}", "info")
            add_log(
                reagent.id,
                current_user.id,
                f"Set order for item {reagent.id} - {reagent.name}",
            )
        except Exception as e:
            flash(f"Error ordering {reagent.id} with error {str(e)}", "danger")
            db.session.rollback()
    else:
        flash(f"Error ordering product with id {str(_id)}", "danger")
        return redirect(url_for("show", _id=_id))
    return redirect(url_for("show", _id=_id, title=reagent.name))


@app.route("/view_orders/", methods=["GET"])
@auth_required()
@roles_required("admin")
def view_orders():
    """view orders"""

    orders = db.session.query(Inventory).filter(Inventory.order > 0)
    if orders.count() > 0:
        return render_template(
            "view_orders.html", reagents=orders, title="Reagents to be purchased"
        )
    flash("No orders pending", "info")
    return render_template(
        "view_orders.html", reagents=orders, title="Reagents to be purchased"
    )


@app.route("/reset_order/<int:_id>/", methods=["GET"])
@auth_required()
@roles_required("admin")
def reset_order(_id):
    """reset order for a specific reagent"""

    reagent = db.session.query(Inventory).filter(Inventory.id == _id).first()
    if reagent:
        if not current_user.has_role(reagent.location.department.short_name):
            flash(
                f"You have not permission to reset order for a reagent in a location pertaining to {reagent.location.department.name}",
                "danger",
            )
            return redirect(url_for("show", _id=_id))

        reagent.order = 0
        try:
            db.session.commit()
            flash("Item orders reset", "info")
            add_log(
                reagent.id,
                current_user.id,
                f"reset orders for item {reagent.id} - {reagent.name}",
            )
        except Exception as e:
            flash(f"Error reset ordering {reagent.id} with error {str(e)}", "danger")
            db.session.rollback()
    else:
        flash(f"Error resetting order product with id: {str(_id)}", "danger")
        return redirect(url_for("show", _id=_id))
    return redirect(url_for("view_orders"))


@app.route("/view_low_quantity/", methods=["GET"])
@auth_required()
@roles_required("admin")
def view_low_quantity():
    """view list of reagent with low quantity"""

    reag = db.session.query(Inventory).filter(
        (Inventory.amount + Inventory.amount2) < Inventory.amount_limit
    )
    if reag.count() > 0:
        return render_template("list_low.html", reagents=reag, title="Low Quantity Report")
    flash("No reagents below minimum stock limits", "info")
    return render_template("list_low.html", reagents=reag, title="Low quantity Report")


@app.route("/view_zero_quantity/", methods=["GET"])
@auth_required()
@roles_required("admin")
def view_zero_quantity():
    """view list of reagent with zero quantity"""

    reag = db.session.query(Inventory).filter(
        (Inventory.amount + Inventory.amount2) == 0
    )
    if reag.count() > 0:
        return render_template("list_zero.html", reagents=reag, title="Zero Quantity Report")
    flash("No reagents with zero amount", "info")
    return render_template("list_zero.html", reagents=reag, title="Zero Quantity Report")


@app.route("/export", methods=["GET"])
@auth_required()
@roles_required("superadmin")
def export():
    """export reagents table as csv"""
    reagents = Inventory.query.all()
    with open((os.path.join(app.config['APP_ROOT'], 'inventory.csv')), "w", newline="", encoding="utf-8") as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=",")
        csvwriter.writerow(
            [
                "Id",
                "Name",
                "Location",
                "amount lab",
                "amount deposit",
                "amount limit",
                "cas_number",
                "product code",
                "supplier",
                "batch",
                "expiry date",
                "size",
                "notes",
                "to be purchased",
            ]
        )
        for r in reagents:
            csvwriter.writerow(
                [
                    r.id,
                    r.name,
                    r.location_id,
                    r.amount,
                    r.amount2,
                    r.amount_limit,
                    r.cas_number,
                    r.product_code,
                    r.supplier,
                    r.batch,
                    r.expiry_date,
                    r.size,
                    r.notes,
                    r.order,
                ]
            )
    try:
        return send_file("inventory.csv", mimetype="text/csv", as_attachment=True)
    except Exception as e:
        return str(e)


@app.route("/stats", methods=["GET"])
@auth_required()
@roles_required("admin")
def stats():

    days = int(request.args.get('days', 365))

    logs = Applog.query.filter(Applog.event_time > (datetime.now() - timedelta(days=days)), Applog.event_time <= datetime.now()).all()
    reag = Inventory.query.all()
    idslist = set()
    for l in logs:
        if l.product_id == None:
            continue
        idslist.add(l.product_id)
    res = {el:0 for el in idslist}
    for i in idslist:
        c = 0
        for l in logs:
            if l.product_id == i:
                if l.event_detail.startswith("updated"):
                    c += 1
        res[i] = c

    title = f"Items consumed in the last { days } days"

    return render_template("stats.html", stats=res, reag=reag, title=title)


