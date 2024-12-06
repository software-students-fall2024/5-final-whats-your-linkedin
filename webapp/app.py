from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generates a random secret key

uri = "mongodb+srv://hugobray01:AmosBloomberg@splitsmart.ursnd.mongodb.net/?retryWrites=true&w=majority&appName=SplitSmart"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

mydb = client["SplitSmart"]
col_users = mydb["USERS"]
col_groups = mydb["GROUPS"]

@app.route('/')
def welcome():
    return render_template('welcome.html')
    
@app.route('/home')
def home():
    if 'username' not in session:
        flash("Plesae log in first.")
        return redirect(url_for('login'))
    return render_template('home.html', username=session['username'])

@app.route('/groups')
def groups():
    if 'username' not in session:
        flash("Plesae log in first.")
        return redirect(url_for('login'))
    return render_template('groups.html')

@app.route('/add-expense')
def add_expense():
    if 'username' not in session:
        flash("Plesae log in first.")
        return redirect(url_for('login'))
    return render_template('add-expense.html')

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if col_users.find_one({"name": username}):
            flash('Username is already in use. Please choose another one.')
            return redirect(url_for('registration'))

        col_users.insert_one({"name": username, "password": password, "groups": []})
        flash("Registration successful! Please Log In.")

        return redirect(url_for('login'))
    return render_template('registration.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = col_users.find_one({"name": username, 'password': password})
        if user:
            session['username'] = username
            flash("Login Success!")
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password.  Try again.")
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out.")
    return redirect(url_for('welcome'))
    
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
