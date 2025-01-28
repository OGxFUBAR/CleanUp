from . import db
from datetime import datetime

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(50), nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default="Pending")
    cleaners = db.relationship('CleanerAssignment', backref='reservation', lazy=True)

class Cleaner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class CleanerAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservation.id'), nullable=False)
    cleaner_id = db.Column(db.Integer, db.ForeignKey('cleaner.id'), nullable=False)

class ManualCleanup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(50), nullable=True)
    type = db.Column(db.String(20), nullable=False)  # 'Unit' or 'Sales'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
