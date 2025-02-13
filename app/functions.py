from datetime import (
    datetime,
    date,
    timedelta,
)

from dateutil.relativedelta import relativedelta

from app import db
from .models import Applog, Inventory, User, CalibrationsLog, Calibrations


def add_log(product_id, user_id, event_detail):
    now = datetime.now()
    product = Inventory.query.filter(Inventory.id == product_id).first()
    user = User.query.filter(User.id == user_id).first()
    logdata = Applog(
        product=product, user=user, event_time=now, event_detail=event_detail
    )
    db.session.add(logdata)
    db.session.commit()


def add_calibration_log(calibration_id, user_id, event_detail):
    now = datetime.now()
    calibration = Calibrations.query.filter(Calibrations.id == calibration_id).first()
    user = User.query.filter(User.id == user_id).first()
    logdata = CalibrationsLog(
        calibration=calibration, user=user, event_time=now, event_detail=event_detail
    )
    db.session.add(logdata)
    db.session.commit()


def calculate_next_calibration_date(_id):
    calibration = db.session.query(Calibrations).filter(Calibrations.id == _id).first()
    freq = int(calibration.frequency)
    freq_units = str(calibration.frequency_units)
    tolerance = int(calibration.tolerance)
    tolerance_units = str(calibration.tolerance_units)

    # se chiamata dal form di editing i campi ritornati sono tutte stringhe
    if isinstance(calibration.initial_check_date, str):
        initc = datetime.strptime(calibration.initial_check_date, "%Y-%m-%d").date()
        lastc = datetime.strptime(calibration.last_calibration_date, "%Y-%m-%d").date()
    else:
        initc = calibration.initial_check_date
        lastc = calibration.last_calibration_date
    run = True
    n = 0
    while run:
        n += 1
        nextc = calculate_relativedelta(initc, freq_units, freq, n)
        if nextc > calculate_relativedelta(lastc, tolerance_units, tolerance, n=1):
            run = False
    return nextc


def calculate_relativedelta(value, unit, increment, n):
    increment = increment * n
    if unit == "days":
        return value + relativedelta(days=+increment)
    if unit == "weeks":
        return value + relativedelta(weeks=+increment)
    if unit == "months":
        return value + relativedelta(months=+increment)
    if unit == "years":
        return value + relativedelta(years=+increment)
