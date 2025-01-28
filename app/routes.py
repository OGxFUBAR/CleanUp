from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from .models import Reservation, CleanerAssignment, Archive, db
from datetime import datetime, timedelta
import pandas as pd
import os
from werkzeug.utils import secure_filename

bp = Blueprint('main', __name__)

# Upload and manage reservations
@bp.route('/reservations', methods=['GET', 'POST'])
def reservations():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            # Save and process the uploaded file
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(file_path)

            try:
                # Process the file
                data = pd.read_csv(file_path) if filename.endswith('.csv') else pd.read_excel(file_path)

                # Validate required columns
                if 'Unit #' not in data.columns or 'Pickup Date' not in data.columns:
                    flash("File must contain 'Unit #' and 'Pickup Date' columns.", "danger")
                    return redirect(url_for('main.reservations'))

                # Update reservations
                for _, row in data.iterrows():
                    vehicle_number = row['Unit #']
                    departure_time = datetime.strptime(row['Pickup Date'], "%m/%d/%Y %I:%M %p")
                    reservation = Reservation.query.filter_by(vehicle_number=vehicle_number).first()

                    if not reservation:
                        reservation = Reservation(vehicle_number=vehicle_number, departure_time=departure_time)
                        db.session.add(reservation)
                    else:
                        reservation.departure_time = departure_time  # Update if reservation exists

                db.session.commit()
                flash("Reservations imported successfully.", "success")
            except Exception as e:
                flash(f"Error processing file: {e}", "danger")

            os.remove(file_path)  # Clean up uploaded file

    # Fetch and update reservation statuses
    now = datetime.now()
    reservations = Reservation.query.all()
    for reservation in reservations:
        delta = (reservation.departure_time - now).total_seconds() / 60  # Minutes until departure
        if delta <= 30:
            reservation.status = "Urgent"
        elif delta <= 60:
            reservation.status = "Important"
        else:
            reservation.status = "Upcoming"
        db.session.commit()

    return render_template('reservations.html', reservations=reservations)

# Manage cleanup list and active cleanups
@bp.route('/cleanup', methods=['GET', 'POST'])
def cleanup():
    if request.method == 'POST':
        vehicle_number = request.form['vehicle_number']
        cleaner_name = request.form['cleaner_name']

        reservation = Reservation.query.filter_by(vehicle_number=vehicle_number).first()
        if reservation:
            # Check if the vehicle is already being cleaned
            active_cleanup = CleanerAssignment.query.filter_by(
                reservation_id=reservation.id, end_time=None
            ).first()

            if active_cleanup:
                flash(f"Vehicle {vehicle_number} is already being cleaned by {active_cleanup.cleaner_name}.", "warning")
            else:
                # Create a new cleaner assignment
                cleaner_assignment = CleanerAssignment(
                    reservation_id=reservation.id,
                    cleaner_name=cleaner_name
                )
                db.session.add(cleaner_assignment)
                db.session.commit()
                flash(f"Cleaner {cleaner_name} is cleaning Unit {vehicle_number}.", "success")
        else:
            flash(f"Vehicle {vehicle_number} not found in reservations.", "danger")

    # Show active cleanups
    active_cleanups = CleanerAssignment.query.filter_by(end_time=None).all()
    return render_template('cleanup.html', active_cleanups=active_cleanups)

# Complete a cleanup
@bp.route('/complete_cleanup/<int:cleanup_id>', methods=['POST'])
def complete_cleanup(cleanup_id):
    cleaner_assignment = CleanerAssignment.query.get(cleanup_id)
    if cleaner_assignment and cleaner_assignment.end_time is None:
        cleaner_assignment.end_time = datetime.now()
        cleaner_assignment.reservation.last_cleaned_at = datetime.now()
        db.session.commit()
        flash(f"Vehicle {cleaner_assignment.reservation.vehicle_number} has been cleaned by {cleaner_assignment.cleaner_name}.", "success")
    else:
        flash("Cleanup not found or already completed.", "danger")

    return redirect(url_for('main.cleanup'))

# Archive old data
def archive_old_data():
    threshold_date = datetime.now() - timedelta(days=30)

    # Archive old reservations
    old_reservations = Reservation.query.filter(Reservation.departure_time < threshold_date).all()
    for res in old_reservations:
        archive_entry = Archive(
            vehicle_number=res.vehicle_number,
            last_cleaned_at=res.last_cleaned_at,
            last_reserved_at=res.departure_time
        )
        db.session.add(archive_entry)
        db.session.delete(res)

    db.session.commit()
