from . import db
from datetime import datetime

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(50), nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default="Pending")
    last_cleaned_at = db.Column(db.DateTime, nullable=True)  # Tracks the last time it was cleaned
    cleaners = db.relationship('CleanerAssignment', backref='reservation', lazy=True)



class Cleaner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class CleanerAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservation.id'), nullable=False)
    cleaner_name = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.DateTime, default=db.func.now())  # When the cleaner started
    end_time = db.Column(db.DateTime, nullable=True)  # When the cleaner completed cleaning
    participants = db.Column(db.String(255), nullable=True)  # Names of helpers (if any)



class ManualCleanup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(50), nullable=True)
    type = db.Column(db.String(20), nullable=False)  # 'Unit' or 'Sales'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Archive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(50), nullable=False)
    last_cleaned_at = db.Column(db.DateTime, nullable=True)
    last_reserved_at = db.Column(db.DateTime, nullable=False)

from flask_login import UserMixin
from . import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin' for admins

