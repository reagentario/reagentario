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
    EditProfileForm,
    EditRolesForm,
    ChangePasswordForm,
    CreateUserForm,
)
from app.models import User, Role

from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError, PendingRollbackError

from flask_security import (
    Security,
    SQLAlchemySessionUserDatastore,
    SQLAlchemyUserDatastore,
    current_user,
    auth_required,
    hash_password,
    permissions_accepted,
    permissions_required,
    roles_accepted,
    roles_required,
    RoleMixin,
    UserMixin,
)

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
app.security = Security(app, user_datastore)

# one time setup
with app.app_context():
    # Create users to test with
    db.create_all()
    if not app.security.datastore.find_role("admin"):
        app.security.datastore.create_role(name="admin",
                                           description="admin role",
                                           permissions="admin"
        )

    if not app.security.datastore.find_role("superadmin"):
        app.security.datastore.create_role(name="superadmin",
                                           description="superadmin role",
                                           permissions="superadmin"
        )

    if not app.security.datastore.find_role("QC"):
        app.security.datastore.create_role(name="QC",
                                           description="QC dept",
                                           permissions="QC"
        )

    if not app.security.datastore.find_role("VL"):
        app.security.datastore.create_role(name="VL",
                                           description="VL dept",
                                           permissions="VL"
        )

    if app.config["CREATE_USERS"]:
        if not app.security.datastore.find_user(email="user@test.com"):
            app.security.datastore.create_user(
                email="user@test.com",
                password=hash_password("password"),
                username="User1",
                active=True,
            )

        if not app.security.datastore.find_user(email="admin@test.com"):
            app.security.datastore.create_user(
                email="admin@test.com",
                password=hash_password("password"),
                username="Admin1",
                roles=["admin"],
                active=True,
            )

        if not app.security.datastore.find_user(email="admin2@test.com"):
            app.security.datastore.create_user(
                email="admin2@test.com",
                password=hash_password("password"),
                username="Admin2",
                roles=["admin", "superadmin"],
                active=True,
            )
    db.session.commit()


@app.route("/edit_profile", methods=["GET", "POST"])
@auth_required()
def edit_profile():
    """edit profile form"""
    form = EditProfileForm()
    try:
        if form.validate_on_submit():
            current_user.email = form.email.data
            current_user.username = form.username.data
            db.session.commit()
            flash("Your changes have been saved.", "info")
            app.logger.info(
                f"user {current_user.id} updated, new email: {current_user.email}, new userame: {current_user.username}"
            )
            return redirect(url_for("edit_profile"))
    except IntegrityError:
        flash(
            "The email or username you choose is already registered, user not updated",
            "danger",
        )
        return redirect(url_for("edit_profile"))
    if request.method == "GET":
        form.email.data = current_user.email
        form.username.data = current_user.username

    return render_template(
        "edit_profile.html", title="Edit Profile", form=form, user=current_user
    )


@app.route("/change_pw/<int:_id>/", methods=["GET", "POST"])
@auth_required()
def change_pw(_id):
    """change password form"""
    if current_user.id == _id or current_user.has_role("superadmin"):
        form = ChangePasswordForm(csrf_enabled=False)
        user = User.query.filter_by(id=_id).first()
        if not user:
            flash(f"Not existing user id {_id}", "danger")
            return redirect(url_for("index"))

        if form.validate_on_submit():
            user.password = hash_password(form.password.data)
            flash(f"Password changed for {user.email}", "info")
            app.logger.info(f"user {user.email} password changed by user {current_user.id}")
            db.session.commit()
            return redirect(url_for("users"))
        return render_template(
            "change_pw.html", title="Change password", form=form, user=user
        )
    else:
        flash(f"You cannot change the password for user {_id}", "danger")
        return redirect(url_for("users"))


@app.route("/users", methods=["GET"])
@auth_required()
@roles_required("superadmin")
def users():
    """return list of users"""
    _users = User.query.all()
    return render_template("users.html", users=_users, title="Users")


@app.route("/edit_role/<int:_id>/", methods=["GET", "POST"])
@auth_required()
@roles_required("superadmin")
def edit_role(_id):
    """edit roles form"""
    form = EditRolesForm()
    user = User.query.filter_by(id=_id).first()
    admin_role = user_datastore.find_role("admin")
    superadmin_role = user_datastore.find_role("superadmin")
    qc_role = user_datastore.find_role("QC")
    vl_role = user_datastore.find_role("VL")
    if not user:
        flash(f"Not existing user id {_id}", "danger")
        return redirect(url_for("users"))
    try:
        if form.validate_on_submit():
            if form.admin.data:
                app.security.datastore.add_role_to_user(user, admin_role)
            else:
                app.security.datastore.remove_role_from_user(user, admin_role)
            if form.superadmin.data:
                app.security.datastore.add_role_to_user(user, superadmin_role)
            else:
                app.security.datastore.remove_role_from_user(user, superadmin_role)
            if form.qc.data:
                app.security.datastore.add_role_to_user(user, qc_role)
            else:
                app.security.datastore.remove_role_from_user(user, qc_role)
            if form.vl.data:
                app.security.datastore.add_role_to_user(user, vl_role)
            else:
                app.security.datastore.remove_role_from_user(user, vl_role)
            db.session.commit()
            flash("Your changes have been saved.", "info")
            app.logger.info(
                f"user {current_user.id} updated by user {current_user.id}, admin role: {form.admin.data}, superadmin role: {form.superadmin.data}, qc role: {form.qc.data}, vl role: {form.vl.data}"
            )
            return redirect(url_for("users"))
        if request.method == "GET":
            if user.has_role("admin"):
                form.admin.data = True
            if user.has_role("superadmin"):
                form.superadmin.data = True
            if user.has_role("QC"):
                form.qc.data = True
            if user.has_role("VL"):
                form.vl.data = True

    except Exception as e:
        flash(f"Error editing {user.id} with error {str(e)}", "danger")
        db.session.rollback()
        return render_template(
            "edit_roles.html", title="Edit User Roles", user=user, form=form
        )

    return render_template(
        "edit_roles.html", title="Edit User Roles", form=form, user=user
    )


@app.route("/edit_user/<int:_id>/", methods=["GET", "POST"])
@auth_required()
@roles_required("superadmin")
def edit_user(_id):
    """edit user form"""
    if current_user.id == _id or current_user.has_role("superadmin"):
        form = EditProfileForm()
        user = User.query.filter_by(id=_id).first()
        if not user:
            flash(f"Not existing user with id {_id}", "danger")
            return redirect(url_for("users"))
        try:
            if form.validate_on_submit():
                user.email = form.email.data
                user.username = form.username.data
                user.active = form.active.data
                db.session.commit()
                flash("Your changes have been saved.", "info")
                app.logger.info(
                    f"user {user.id} updated by user {current_user.id}, email: {user.email}, username: {user.username}, active: {user.active}"
                )
                return redirect(url_for("users"))
        except IntegrityError:
            flash("Email or username already registered, user not updated", "danger")
            return redirect(url_for("users"))
        if request.method == "GET":
            form.email.data = user.email
            form.username.data = user.username
            form.active.data = user.active
        return render_template(
            "edit_user.html", title="Edit User", form=form, user=user
        )
    flash(f"You cannot change data for user {_id}", "danger")
    return redirect(url_for("users"))


@app.route("/create_user", methods=["GET", "POST"])
@auth_required()
@roles_required("superadmin")
def create_user():
    """create a new user"""

    form = CreateUserForm()

    if request.method == "POST":
        try:
            if form.validate_on_submit():
                email = request.form["email"]
                username = request.form["username"]
                password = hash_password(request.form["password"])
                admin = form.data.get("admin")
                superadmin = form.data.get("superadmin")
                qc = form.data.get("qc")
                vl = form.data.get("vl")
                admin_role = user_datastore.find_role("admin")
                superadmin_role = user_datastore.find_role("superadmin")
                qc_role = user_datastore.find_role("QC")
                vl_role = user_datastore.find_role("VL")

                existing_user = User.query.filter(
                    User.email == email or User.username == username
                ).first()
                if existing_user:
                    flash(
                        f"A User with this email ({email}) or username ({username}) already exists!",
                        "danger",
                    )
                    return render_template(
                        "create_user.html", title="Add a new user", form=form
                    )
                app.security.datastore.create_user(
                    email=email,
                    password=password,
                    username=username,
                    active=True,
                )
                user = User.query.filter_by(username=username).first()
                if admin:
                    app.security.datastore.add_role_to_user(user, admin_role)
                if superadmin:
                    app.security.datastore.add_role_to_user(user, superadmin_role)
                if qc:
                    app.security.datastore.add_role_to_user(user, qc_role)
                if vl:
                    app.security.datastore.add_role_to_user(user, vl_role)

                db.session.commit()
                app.logger.info(f"created user {email} by user {current_user.id}")
                return redirect(url_for("users"))
        except Exception as e:
            flash(f"Error creating {user.id} with error {str(e)}", "danger")
            db.session.rollback()
            return render_template(
                "create_user.html", title="Add a new user", user=user, form=form
            )
    return render_template("create_user.html", title="Add a new user", form=form)


@app.route("/delete_user/<int:_id>/", methods=["GET"])
@auth_required()
@roles_required("superadmin")
def delete_user(_id):
    """delete a user"""
    user = db.session.query(User).filter(User.id == _id).first()
    if user:
        try:
            db.session.delete(user)
            db.session.commit()
            flash("User deleted", "info")
            app.logger.info(f"deleted user id {user.id} (email: {user.email}) by user {current_user.id} (email: {current_user.email})")
        except Exception as e:
            flash(f"Error deleting user id {str(user.id)} with error {str(e)}", "danger")
            db.session.rollback()
    else:
        flash(f"Error deleting user with id: {str(user.id)}", "danger")
        return redirect(url_for("users"))
    return redirect(url_for("users"))
