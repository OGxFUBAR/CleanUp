from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from .utils import process_excel
from .models import Reservation, ManualCleanup, db
import pandas as pd
import os
from werkzeug.utils import secure_filename
from datetime import datetime

bp = Blueprint('main', __name__)

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

    # Fetch reservations with dynamic status
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

