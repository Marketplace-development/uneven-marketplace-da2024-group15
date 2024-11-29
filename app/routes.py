from flask import Blueprint, request, redirect, url_for, render_template
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
    return render_template('index.html', username=None)

@main.route('/login')
def login():
    return render_template('login.html')

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

    # GET: Toon registratiepagina
    return render_template('register.html')

@main.route('/listings')
def listings():
    return render_template('listings.html')









