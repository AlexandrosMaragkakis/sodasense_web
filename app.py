# Import flask and other modules
from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import requests
import json

# Create an app instance
app = Flask(__name__)

# Configure a secret key for the app
app.secret_key = 'secret'

# Create a login manager instance
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Create a user class that inherits from UserMixin
class User(UserMixin):
    def __init__(self, id):
        self.id = id
        self.name = "user" + str(id)

    def __repr__(self):
        return "%d/%s" % (self.id, self.name)

# Create a user object
user = User(1)

# Define a user loader callback for flask-login
@login_manager.user_loader
def load_user(user_id):
    return user

# Define a route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    # If the request method is POST, send the user credentials to keycloak and check the response
    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        url = 'https://api.sodasense.uop.gr/v1/userLogin'
        data = {
            "username": username,
            "password": password
        }
        headers = {'Content-Type': 'application/json'}

        response = requests.post(url, data=json.dumps(data), headers=headers)
        
        # If the response status code is 200, log in the user and redirect to the index page
        if response.status_code == 200 and response.reason == 'OK' and 'Invalid user credentials' not in response.text:
            login_user(user)
            return redirect(url_for('index'))
        # Otherwise, show an error message
        else:
            print(response.text)
            return render_template('login.html', error='Invalid credentials')
    # If the request method is GET, show the login page
    else:
        return render_template('login.html')

# Define a route for the index page
@app.route('/index')
@login_required
def index():
    # Show the index page
    return render_template('index.html')

# Define a route for the logout page
@app.route('/logout')
@login_required
def logout():
    # Log out the user and redirect to the login page
    logout_user()
    return redirect(url_for('login'))

# Run the app
if __name__ == '__main__':
    app.run(debug=True)