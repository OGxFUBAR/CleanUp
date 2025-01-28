import pandas as pd
from datetime import datetime
from .models import Reservation, db

def process_excel(file_path):
    data = pd.read_excel(file_path)
    for _, row in data.iterrows():
        reservation = Reservation(
            vehicle_number=row['Vehicle Number'],
            departure_time=datetime.strptime(row['Departure Time'], '%Y-%m-%d %H:%M:%S')
        )
        db.session.add(reservation)
    db.session.commit()
