# Import flask and other modules
import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import requests
import json
import base64


API_URL = 'http://192.168.48.222/fake-api/dashboard_services/charts.php'


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


            ####################################################
            token_parts = response.text.split('.')
            map = json.loads(response.text)


            #####################
            tmp = token_parts[2].split(',')
            tmp[0] = tmp[0].replace('"', '')
            access_token = str(map['access_token'])
            #print('Ti tipos einai to token ' + access_token)
            session['access_token'] = access_token

            ## Important!
            if len(token_parts[1]) % 4 == 1:
                token_parts[1] = token_parts[1] + '==='
            elif len(token_parts[1]) % 4 == 2:
                token_parts[1] = token_parts[1] + '=='
            elif len(token_parts[1]) % 4 == 3:
                token_parts[1] = token_parts[1] + '='
            jsontext = base64.b64decode(token_parts[1])
            decoded_token = json.loads(jsontext.decode('utf-8'))
            session['userid'] = decoded_token['sub']
            ####################################################

            login_user(user)
            return redirect(url_for('index'))
        # Otherwise, show an error message
        else:
            #print(response.text)
            return render_template('login.html', error='Invalid credentials.')
    # If the request method is GET, show the login page
    else:
        return render_template('login.html')

# Define a route for the index page
@app.route('/')
@login_required
def index():
    userid = session.get('userid')
    heatmap_filepath = f"static/tmp/{userid}_heatmap.html"
    timed_heatmap_filepath = f"static/tmp/{userid}_timed_heatmap.html"

    if not os.path.exists(heatmap_filepath) and not os.path.exists(timed_heatmap_filepath):
        return render_template('index.html', load_heatmap=True, load_timed_heatmap=True)
    elif not os.path.exists(heatmap_filepath):
        return render_template('index.html', load_heatmap=True, load_timed_heatmap=False, timed_heatmap_file=timed_heatmap_filepath)
    elif not os.path.exists(timed_heatmap_filepath):
        return render_template('index.html', load_heatmap=False, load_timed_heatmap=True, heatmap_file=heatmap_filepath)
    else:
        return render_template('index.html', heatmap_file=heatmap_filepath, timed_heatmap_file=timed_heatmap_filepath)

# endpoint to fetch heatmap asychronously
@app.route('/fetch_heatmap', methods=['POST'])
def fetch_heatmap():
    userid = session.get('userid')
    heatmap_filepath = f"static/tmp/{userid}_heatmap.html"

    if not os.path.exists(heatmap_filepath):
        access_token = session.get('access_token')
        
        headers = {
            'Authorization': 'Bearer ' + access_token,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        payload = {
            "userId": userid,
        }
        response = requests.post(API_URL, headers=headers, json=payload)

        if response.status_code == 200:
            with open(heatmap_filepath, "w") as f:
                f.write(response.text)
        else:
            # Handle the error by returning an error response
            return {'error': 'An error occurred while fetching the heatmap.'}

    # Return the heatmap file path in the response
    return {'filepath': heatmap_filepath}

@app.route('/fetch_chart', methods=['POST'])
def fetch_chart():
    userid = session.get('userid')
    chart_name = request.json.get('chartName')
    chart_filepath = f"static/tmp/{userid}_{chart_name}.html"

    if not os.path.exists(chart_filepath):
        access_token = session.get('access_token')
        
        headers = {
            'Authorization': 'Bearer ' + access_token,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        payload = {
            "userId": userid,
            "chartName": chart_name
        }
        response = requests.post(API_URL, headers=headers, json=payload)

        if response.status_code == 200:
            with open(chart_filepath, "w") as f:
                f.write(response.text)
        else:
            # Handle the error by returning an error response
            return {'error': 'An error occurred while fetching the chart.'}

    # Return the chart file path in the response
    return {'filepath': chart_filepath}



# Define a route for the logout page
@app.route('/logout')
@login_required
def logout():
    # Log out the user and redirect to the login page
    logout_user()
    return redirect(url_for('login'))

@app.errorhandler(404)
def page_not_found(e):
    if request.path.startswith('/fetch_heatmap'):
        return jsonify(error="An error occurred while fetching the heatmap."), 404
    else:
        return render_template('404.html'), 404

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
