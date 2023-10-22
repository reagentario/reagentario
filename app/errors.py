from flask import (
      render_template,
  )

from app import app

# Handling error 404 and displaying relevant web page
@app.errorhandler(404)
def not_found_error(error):
    return render_template("error.html", error_code=404, error_message="Not Found"), 404


# Handling error 500 and displaying relevant web page
@app.errorhandler(500)
def internal_error(error):
    return (
        render_template(
            "error.html", error_code=500, error_message="Internal Server Error"
        ),
        500,
    )


# Handling error 400 and displaying relevant web page
@app.errorhandler(400)
def bad_request_error(error):
    return (
        render_template("error.html", error_code=400, error_message="Bad request"),
        400,
    )


# Handling error 401 and displaying relevant web page
@app.errorhandler(401)
def not_auth_error(error):
    return (
        render_template("error.html", error_code=401, error_message="Unauthorized"),
        401,
    )
