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
            # Save uploaded file
            upload_folder = os.path.join(os.getcwd(), 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            filename = secure_filename(file.filename)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)

            # Process CSV or Excel
            try:
                if filename.endswith('.csv'):
                    data = pd.read_csv(file_path)
                elif filename.endswith('.xlsx'):
                    data = pd.read_excel(file_path)
                else:
                    flash("Unsupported file type. Please upload a CSV or Excel file.", "danger")
                    return redirect(url_for('main.reservations'))

                # Validate required columns
                if 'Vehicle Number' not in data.columns or 'Departure Time' not in data.columns:
                    flash("The file must contain 'Vehicle Number' and 'Departure Time' columns.", "danger")
                    return redirect(url_for('main.reservations'))

                # Save data to the database
                for _, row in data.iterrows():
                    vehicle_number = row['Vehicle Number']
                    departure_time = datetime.strptime(row['Departure Time'], "%Y-%m-%d %H:%M:%S")
                    reservation = Reservation(
                        vehicle_number=vehicle_number,
                        departure_time=departure_time,
                        status="Pending"
                    )
                    db.session.add(reservation)

                db.session.commit()
                flash("File uploaded and reservations added successfully!", "success")
            except Exception as e:
                flash(f"Error processing file: {e}", "danger")

            # Clean up uploaded file
            os.remove(file_path)

    # Retrieve all reservations to display
    reservations = Reservation.query.all()
    return render_template('reservations.html', reservations=reservations)
