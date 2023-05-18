import datetime
from app import db
from .models import Applog, Inventory, User
now = datetime.datetime.now()

def add_log(product_id, user_id, event_detail):
    """ add a log in the db """
    product = Inventory.query.filter(Inventory.id==product_id).first()
    user = User.query.filter(User.id==user_id).first()
    log = Applog(product=product,
                    user=user,
                    event_time=now,
                    event_detail=event_detail)
    db.session.add(log)
    db.session.commit()
