from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from .models import Reservation, CleanerAssignment, Archive, db
from datetime import datetime, timedelta
import pandas as pd
import os
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from flask_migrate import upgrade


bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    return redirect(url_for('main.reservations'))


# Upload and manage reservations
@bp.route('/reservations', methods=['GET', 'POST'])
def reservations():
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)

            if os.path.exists(file_path):
                flash(f"File '{filename}' already uploaded.", "warning")
                return redirect(url_for('main.reservations'))

            file.save(file_path)

            try:
                # Process the file
                data = pd.read_csv(file_path) if filename.endswith('.csv') else pd.read_excel(file_path)

                # Validate required columns
                required_columns = {'Unit #', 'Pickup Date'}
                if not required_columns.issubset(data.columns):
                    flash(f"File must contain the following columns: {', '.join(required_columns)}", "danger")
                    return redirect(url_for('main.reservations'))

                # Update reservations
                for _, row in data.iterrows():
                    vehicle_number = row['Unit #']
                    try:
                        departure_time = parser.parse(row['Pickup Date'])
                    except Exception:
                        flash(f"Invalid date format for vehicle {vehicle_number}.", "danger")
                        continue

                    reservation = Reservation.query.filter_by(vehicle_number=vehicle_number).first()
                    if not reservation:
                        reservation = Reservation(vehicle_number=vehicle_number, departure_time=departure_time)
                        db.session.add(reservation)
                    else:
                        reservation.departure_time = departure_time  # Update existing reservation

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

    db.session.commit()  # Commit all updates

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


@bp.route('/logs')
@login_required
def logs():
    if current_user.role != 'admin':
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('main.reservations'))
    # Display logs
    return render_template('logs.html')

@bp.route('/cleanup_logs')
@login_required
def cleanup_logs():
    if current_user.role != 'admin':
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('main.reservations'))

    logs = CleanerAssignment.query.order_by(CleanerAssignment.start_time.desc()).all()
    return render_template('cleanup_logs.html', logs=logs)

@bp.route('/migratedb', methods=['GET'])
def migrate_db():
    try:
        from flask_migrate import init, migrate, upgrade

        # Check if the migrations directory exists
        migrations_path = os.path.join(current_app.root_path, 'migrations')
        if not os.path.exists(migrations_path):
            init()  # Initialize the migrations folder

        # Check if a migration file exists
        migration_files = os.listdir(migrations_path)
        if len(migration_files) <= 1:  # Only the script folder and README
            migrate(message="Initial migration")  # Create initial migration

        upgrade()  # Apply the migration
        return jsonify({"status": "success", "message": "Database migration complete!"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
