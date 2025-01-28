from flask import Blueprint, render_template, request, redirect, url_for, flash
from . import db
from .models import Reservation, Cleaner, ManualCleanup, CleanerAssignment
from datetime import datetime
import os
import pandas as pd

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/reservations', methods=['GET', 'POST'])
def reservations():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            data = pd.read_excel(file_path)
            for _, row in data.iterrows():
                reservation = Reservation(
                    vehicle_number=row['Vehicle Number'],
                    departure_time=datetime.strptime(row['Departure Time'], '%Y-%m-%d %H:%M:%S')
                )
                db.session.add(reservation)
            db.session.commit()
            flash('Reservations imported successfully', 'success')
        return redirect(url_for('main.reservations'))

    reservations = Reservation.query.all()
    return render_template('reservations.html', reservations=reservations)

@bp.route('/manual_cleanup', methods=['GET', 'POST'])
def manual_cleanup():
    if request.method == 'POST':
        type = request.form['type']
        vehicle_number = request.form['vehicle_number'] if type == 'Unit' else None
        manual_cleanup = ManualCleanup(vehicle_number=vehicle_number, type=type)
        db.session.add(manual_cleanup)
        db.session.commit()
        flash('Manual cleanup recorded successfully', 'success')
        return redirect(url_for('main.manual_cleanup'))

    return render_template('manual_cleanup.html')

@bp.route('/logs')
def logs():
    cleanups = ManualCleanup.query.order_by(ManualCleanup.created_at.desc()).all()
    return render_template('logs.html', cleanups=cleanups)

@bp.route('/stats')
def stats():
    # Calculate stats here
    return render_template('stats.html')
