from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from .utils import process_excel
from .models import Reservation, ManualCleanup, db
import os

bp = Blueprint('main', __name__)

@bp.route('/reservations', methods=['GET', 'POST'])
def reservations():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            process_excel(file_path)
            flash('Reservations imported successfully', 'success')
            os.remove(file_path)  # Clean up the file after processing
        return redirect(url_for('main.reservations'))

    reservations = Reservation.query.all()
    return render_template('reservations.html', reservations=reservations)
