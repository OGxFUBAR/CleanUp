from . import db
from datetime import datetime

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Primary key for the reservation
    vehicle_number = db.Column(db.String(50), nullable=False)  # The vehicle's unique identifier
    departure_time = db.Column(db.DateTime, nullable=False)  # When the vehicle departs
    status = db.Column(db.String(20), default="Pending")  # The status of the reservation (e.g., Pending, Completed)
    cleaners = db.relationship('CleanerAssignment', backref='reservation', lazy=True)  
    # One-to-many relationship with CleanerAssignment


class Cleaner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class CleanerAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Primary key for cleaner assignments
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservation.id'), nullable=False)  
    # Foreign key linking to the Reservation model
    cleaner_name = db.Column(db.String(100), nullable=False)  # Name of the cleaner
    assigned_at = db.Column(db.DateTime, default=db.func.now())  # Timestamp of the assignment


class ManualCleanup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(50), nullable=True)
    type = db.Column(db.String(20), nullable=False)  # 'Unit' or 'Sales'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
