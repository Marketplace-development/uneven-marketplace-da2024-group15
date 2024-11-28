from flask import Blueprint, request, redirect, url_for, render_template, session
from datetime import datetime
from .models import db, User
from .models import db, ParkingSpot
from .models import db, Transaction

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        listings = ParkingSpot.query.filter_by(user_id=user.id).all() 
        return render_template('index.html', username=user.username, listings=listings)
    return render_template('index.html', username=None)




