# Import flask and other modules
import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import requests
import json
import base64


API_URL = 'http://192.168.48.222/fake-api/dashboard_services/charts.php'


# Create an app instance
app = Flask(__name__)

# Set the session timeout to 1 hour (3600 seconds)
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

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


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    View function to handle GET and POST requests to '/login'.
    For GET requests, it returns the login page.
    For POST requests, it sends the user credentials to an API and logs in the user if the credentials are valid.

    Returns:
        GET request: login page
        POST request with valid credentials: index page
        POST request with invalid credentials: login page with error message
    """

    if request.method == 'POST':
        # Extracting the username and password from the form data
        username = request.form['username']
        password = request.form['password']

        # Sending the user credentials to an API
        url = 'https://api.sodasense.uop.gr/v1/userLogin'
        data = {
            "username": username,
            "password": password
        }
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, data=json.dumps(data), headers=headers)

        # Checking if the API response contains a valid access token
        if response.status_code == 200 and response.reason == 'OK' and 'Invalid user credentials' not in response.text:

            # Parsing the token from the API response
            token_parts = response.text.split('.')
            map = json.loads(response.text)
            tmp = token_parts[2].split(',')
            tmp[0] = tmp[0].replace('"', '')
            access_token = str(map['access_token'])
            session['access_token'] = access_token

            # Decoding the token and extracting user information
            if len(token_parts[1]) % 4 == 1:
                token_parts[1] = token_parts[1] + '==='
            elif len(token_parts[1]) % 4 == 2:
                token_parts[1] = token_parts[1] + '=='
            elif len(token_parts[1]) % 4 == 3:
                token_parts[1] = token_parts[1] + '='
            jsontext = base64.b64decode(token_parts[1])
            decoded_token = json.loads(jsontext.decode('utf-8'))
            session['userid'] = decoded_token['sub']
            session['chart_filepath'] = f"static/tmp/{session['userid']}_heatmap.html"

            # Logging in the user and redirecting to the index page
            login_user(user)
            return redirect(url_for('index'))

        # Showing an error message if the API response contains invalid credentials
        else:
            return render_template('login.html', error='Invalid credentials.')

    # Returning the login page for GET requestsΠ
    else:
        return render_template('login.html')


@app.route('/')
@login_required
def index():
    """
    A view function that is responsible for rendering the index.html template. 
    It is decorated with the route '/' and the login_required decorator to 
    ensure that only authenticated users can access it. 

    The function does not take any parameters and returns the rendered index.html template.
    """
    return render_template('index.html')


@app.route('/sensors')
@login_required
def sensors():
    """
    A view function that is responsible for rendering the sensors.html template. 
    It is decorated with the route '/sensors' and the login_required decorator to 
    ensure that only authenticated users can access it. 

    The function does not take any parameters and returns the rendered sensors.html template.
    """
    return render_template('sensors.html')


@app.route('/fetch_chart', methods=['POST'])
@login_required
def fetch_chart():
    """
    Endpoint for fetching a chart given a chart name, start and end timestamps.

    Returns:
        {'success': True, 'filepath': chart_filepath} if successful.
        {'success': False, 'error': f'{info}'} if an error occurs.
    """
    userid = session.get('userid')
    chart_name = request.json.get('chartName')
    chart_filepath = f"static/tmp/{userid}_{chart_name}.html"

    # Retrieve start and end timestamps from the request
    startTimestamp = request.json.get('startTimestamp')
    endTimestamp = request.json.get('endTimestamp')

    # Remove existing chart file if it exists
    if os.path.exists(chart_filepath):
        os.remove(chart_filepath)

    # Send request to the API to fetch the chart data
    access_token = session.get('access_token')
    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    payload = {
        "userId": userid,
        "chartName": chart_name,
        "startTimestamp": startTimestamp,
        "endTimestamp": endTimestamp
    }
    response = requests.post(API_URL, headers=headers, json=payload)

    # Process the response from the API
    if response.status_code == 200:
        # Write the chart data to a file
        with open(chart_filepath, "w") as f:
            f.write(response.text.replace('{"status":"OK"}', ''))
    else:
        # Handle the error by returning an error response
        data = response.json()
        info = data.get('info')
        return {'success': False, 'error': f'{info}'}

    # Return the success response with chart file path
    return {'success': True, 'filepath': chart_filepath}


# Define a route for the logout page
@app.route('/logout')
@login_required
def logout():
    """
    Route to log out the user and remove their heatmap chart file.

    Returns:
        redirect: Redirects to the login page.
    """
    # Define the chart file path
    chart_filepath = f"static/tmp/{session['userid']}_heatmap.html"

    # Log out the user
    logout_user()

    # Remove the user's heatmap chart file if it exists
    if os.path.exists(chart_filepath):
        os.remove(chart_filepath)

    # Redirect to the login page
    return redirect(url_for('login'))


@app.errorhandler(404)
def page_not_found(e):
    """
    Handles 404 errors when a page is not found.
    """
    if request.path.startswith('/fetch_heatmap'):
        # Return a JSON response with an error message and a 404 status code
        return jsonify(error="An error occurred while fetching the heatmap."), 404
    else:
        # Render the 404.html template with a 404 status code
        return render_template('404.html'), 404


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
