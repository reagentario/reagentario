import datetime
from app import db
from app import log
from .models import Applog, Inventory, User, CalibrationsLog, Calibrations
from datetime import (
    datetime,
    date,
    timedelta,
)


def add_log(product_id, user_id, event_detail):
    now = datetime.now()
    product = Inventory.query.filter(Inventory.id == product_id).first()
    user = User.query.filter(User.id == user_id).first()
    logdata = Applog(product=product, user=user, event_time=now, event_detail=event_detail)
    db.session.add(logdata)
    db.session.commit()


def add_calibration_log(calibration_id, user_id, event_detail):
    now = datetime.now()
    calibration = Calibrations.query.filter(Calibrations.id == calibration_id).first()
    user = User.query.filter(User.id == user_id).first()
    logdata = CalibrationsLog(calibration=calibration, user=user, event_time=now, event_detail=event_detail)
    db.session.add(logdata)
    db.session.commit()


def calculate_next_calibration_date(_id):
    calibration = db.session.query(Calibrations).filter(Calibrations.id == _id).first()
    freq = int(calibration.frequency)
    tolerance = int(calibration.tolerance)
    #se chiamata dal form di editing i campi ritornati sono tutte stringhe
    if isinstance(calibration.initial_check_date, str):
        nextc = datetime.strptime(calibration.initial_check_date, '%Y-%m-%d').date()
        lastc = datetime.strptime(calibration.last_calibration_date, '%Y-%m-%d').date()
    else:
        nextc = calibration.initial_check_date
        lastc = calibration.last_calibration_date
    run = True
    while run:
        nextc = nextc + timedelta(days=freq)
        if nextc > lastc + timedelta(days=tolerance):
            run = False
    return nextc
