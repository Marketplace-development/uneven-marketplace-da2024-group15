from flask import Blueprint, request, redirect, url_for, render_template, session, flash
from .models import db, User
from supabase import create_client

# Blueprint instellen
main = Blueprint('main', __name__)

# Supabase configureren met de gegevens uit je Config
SUPABASE_URL = "https://dtdwcwplnobtjbstnqxd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR0ZHdjd3Bsbm9idGpic3RucXhkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzA4MDU1MTcsImV4cCI6MjA0NjM4MTUxN30.40ImlI3NoiA5wEs6Sp6EPwJBPA-u-dualZVxZ22isdw"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@main.route('/')
def index():
    username = session.get('username')  # Get the username from the session
    return render_template('index.html', username=username)

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Haal gegevens uit het formulier
        username = request.form.get('username')
        phonenumber = request.form.get('phonenumber')

        # Validatie: Controleer in de lokale database
        if User.query.filter_by(username=username).first():
            return "Username already taken!", 400
        if User.query.filter_by(phonenumber=phonenumber).first():
            return "Phone number already in use!", 400

        # Validatie: Controleer in Supabase
        response = supabase.table('user').select('*').eq('username', username).execute()
        if response.data:
            return "Username already exists in Supabase!", 400

        # Voeg gebruiker toe aan de lokale database
        new_user = User(username=username, phonenumber=phonenumber)
        db.session.add(new_user)
        db.session.commit()

        # Voeg gebruiker toe aan Supabase
        supabase.table('user').insert({
            'username': username,
            'phonenumber': phonenumber
        }).execute()

        # Redirect naar login-pagina
        return redirect(url_for('main.login'))

    return render_template('register.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        
        # Controleer of de gebruikersnaam bestaat in de lokale database
        user = User.query.filter_by(username=username).first()
        
        if user:  # Gebruiker gevonden
            session['username'] = username  # Sla de gebruikersnaam op in de sessie
            flash("You are now logged in", "success")
            return redirect(url_for('main.index'))  # Stuur gebruiker terug naar de hoofdpagina
        else:
            flash("This username does not exist", "danger")
            return redirect(url_for('main.login'))

    return render_template('login.html')

@main.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)  # Verwijder de gebruikersnaam uit de sessie
    flash("You have been logged out", "success")
    return redirect(url_for('main.index'))


@main.route('/listings')
def listings():
    # Your code for listings view
    return render_template('listings.html')
