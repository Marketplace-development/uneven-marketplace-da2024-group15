from flask import Blueprint, request, redirect, url_for, render_template, session, flash
from .models import db, User, Host, Customer, ParkingSpot, Transaction, Review, Availability
from supabase import create_client
from datetime import datetime

# Blueprint instellen
main = Blueprint('main', __name__)

# Supabase configureren met de gegevens uit je Config
SUPABASE_URL = "https://dtdwcwplnobtjbstnqxd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR0ZHdjd3Bsbm9idGpic3RucXhkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzA4MDU1MTcsImV4cCI6MjA0NjM4MTUxN30.40ImlI3NoiA5wEs6Sp6EPwJBPA-u-dualZVxZ22isdw"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@main.route('/')
def login():
    """
    Startpagina: toont de loginpagina.
    Als een gebruiker al ingelogd is, wordt deze doorgestuurd naar de dashboardpagina.
    """
    if 'username' in session:
        return redirect(url_for('main.index'))
    return render_template('login.html')

@main.route('/login', methods=['GET', 'POST'])
def login_post():
    """
    Verwerkt de login van de gebruiker. Controleert de lokale database op de ingevoerde gebruikersnaam.
    Als succesvol, wordt de gebruiker doorgestuurd naar de dashboardpagina (index).
    """
    if request.method == 'POST':
        username = request.form.get('username')
        
        # Controleer of de gebruikersnaam bestaat in de lokale database
        user = User.query.filter_by(username=username).first()
        
        if user:  # Gebruiker gevonden
            session['username'] = username  # Sla de gebruikersnaam op in de sessie
            flash("You are now logged in", "success")
            return redirect(url_for('main.index'))
        else:
            flash("This username does not exist", "danger")
            return redirect(url_for('main.login'))

    return render_template('login.html')

@main.route('/logout', methods=['POST'])
def logout():
    """
    Verwerkt het uitloggen van de gebruiker. De sessie wordt gewist en de gebruiker
    wordt teruggestuurd naar de loginpagina.
    """
    session.pop('username', None)
    flash("You have been logged out", "success")
    return redirect(url_for('main.login'))

@main.route('/index')
def index():
    """
    Dashboardpagina die alleen toegankelijk is als een gebruiker is ingelogd.
    """
    if 'username' not in session:
        return redirect(url_for('main.login'))
    
    username = session['username']
    user = User.query.filter_by(username=username).first()

    # Haal alle parkeerplaatsen op die beschikbaar zijn
    active_listings = db.session.query(ParkingSpot, Availability).join(Availability).all()

    return render_template('index.html', username=username, active_listings=active_listings)


@main.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registratiepagina. Voegt nieuwe gebruikers toe aan de database en registreert deze in Supabase.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        phonenumber = request.form.get('phonenumber')

        print(f"Received username: {username}, phonenumber: {phonenumber}")  # Debug

        # Validatie: Controleer in de lokale database
        if User.query.filter_by(username=username).first():
            flash(f"Username '{username}' already exists in the local database!", "danger")
            return redirect(url_for('main.register'))
        if User.query.filter_by(phonenumber=phonenumber).first():
            flash(f"Phone number '{phonenumber}' already exists in the local database!", "danger")
            return redirect(url_for('main.register'))

        # Validatie: Controleer in Supabase
        response = supabase.table('user').select('username').eq('username', username).execute()
        print(f"Supabase check response: {response.data}")  # Debugging
        if response.data and len(response.data) > 0:
            flash(f"Username '{username}' already exists in Supabase!", "danger")
            return redirect(url_for('main.register'))

        # Voeg gebruiker toe aan Supabase met upsert
        try:
            response = supabase.table('user').upsert({
                'username': username,
                'phonenumber': phonenumber
            }).execute()
            print(f"User successfully added or updated in Supabase: {response.data}")  # Debugging
        except Exception as e:
            print(f"Supabase upsert error: {e}")  # Debugging
            flash("An error occurred while registering in Supabase.", "danger")
            return redirect(url_for('main.register'))

        # Controleer opnieuw in de lokale database voordat je invoegt
        if not User.query.filter_by(username=username).first():
            try:
                new_user = User(username=username, phonenumber=phonenumber)
                db.session.add(new_user)
                db.session.commit()
                print("User successfully added to local database.")  # Debugging
            except Exception as e:
                print(f"Local database insert error: {e}")  # Debugging
                flash("An error occurred while registering in the local database.", "danger")
                return redirect(url_for('main.register'))
        else:
            print(f"User '{username}' already exists in the local database after Supabase sync.")  # Debugging

        # Sla de gebruikersnaam op in de sessie
        session['username'] = username

        flash('Registration successful! Welcome to Rent My Spot!', "success")

        # Redirect naar de index-pagina
        return redirect(url_for('main.index'))

    return render_template('register.html')

@main.route('/listings')
def listings():
    """
    Pagina voor alle beschikbare parkeerplaatsen (voorbeeldimplementatie).
    """
    if 'username' not in session:
        flash("You need to be logged in to view listings.", "danger")
        return redirect(url_for('main.login'))
    
    username = session['username']
    user = User.query.filter_by(username=username).first()
    listings = ParkingSpot.query.filter_by(host_id=user.phonenumber).all()

    return render_template('listings.html', listings=listings)

@main.route('/add_listing', methods=['GET', 'POST'])
def add_listing():
    """
    Pagina voor het toevoegen van een nieuwe parkeerplaats. Vereist login.
    """
    if 'username' not in session:
        flash("You need to be logged in to add a listing.", "danger")
        return redirect(url_for('main.login'))

    username = session.get('username')
    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found in the local database.", "danger")
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        location = request.form.get('location')

        # Controleer of de gebruiker een Host is
        host = Host.query.filter_by(phonenumber=user.phonenumber).first()
        if not host:
            # Voeg toe als Host als dat nog niet is gedaan
            host = Host(phonenumber=user.phonenumber)
            db.session.add(host)
            db.session.commit()

        try:
            # Voeg de nieuwe parkeerplaats toe aan de database
            new_parking_spot = ParkingSpot(
                name=name,
                description=description,
                location=location,
                host_id=host.phonenumber  # phonenumber van de ingelogde gebruiker
            )
            db.session.add(new_parking_spot)
            db.session.commit()

            flash("Parking spot successfully added!", "success")
            return redirect(url_for('main.index'))

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while adding the parking spot: {e}", "danger")
            return redirect(url_for('main.add_listing'))

    return render_template('add_listing.html')

@main.route('/account')
def account():
    """
    Accountpagina: toont gebruikersinformatie en listings van de gebruiker.
    """
    if 'username' not in session:
        flash("You need to be logged in to view your account.", "danger")
        return redirect(url_for('main.login'))

    username = session['username']
    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found in the database.", "danger")
        return redirect(url_for('main.index'))

    # Ophalen van listings van de gebruiker
    listings = ParkingSpot.query.filter_by(host_id=user.phonenumber).all()

    return render_template('account.html', user=user, listings=listings)

@main.route('/make_available/<int:parking_spot_id>', methods=['GET', 'POST'])
def make_available(parking_spot_id):
    """
    Route to mark a parking spot as available by adding availability slots.
    """
    if 'username' not in session:
        flash("You need to be logged in to perform this action.", "danger")
        return redirect(url_for('main.login'))

    username = session['username']
    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found in the database.", "danger")
        return redirect(url_for('main.index'))

    parking_spot = ParkingSpot.query.get(parking_spot_id)
    if not parking_spot or parking_spot.host_id != user.phonenumber:
        flash("Parking spot not found or you do not have permission to modify it.", "danger")
        return redirect(url_for('main.account'))

    if request.method == 'POST':
        starttime = request.form.get('starttime')
        endtime = request.form.get('endtime')
        price = request.form.get('price')

        if not starttime or not endtime or not price:
            flash("Please provide valid availability details.", "danger")
            return redirect(url_for('main.make_available', parking_spot_id=parking_spot_id))

        try:
            # Voeg beschikbaarheid toe aan de database
            availability = Availability(
                starttime=datetime.strptime(starttime, "%Y-%m-%dT%H:%M"),
                endtime=datetime.strptime(endtime, "%Y-%m-%dT%H:%M"),
                parkingspot_id=parking_spot_id,
                price=price
            )
            db.session.add(availability)
            db.session.commit()

            flash("Availability successfully added!", "success")
            return redirect(url_for('main.account'))  # Terug naar accountpagina na succesvolle opslag

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", "danger")
            return redirect(url_for('main.make_available', parking_spot_id=parking_spot_id))

    return render_template('make_available.html', parking_spot=parking_spot)

