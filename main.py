from flask import Flask
from flask import render_template, request, redirect, url_for, session, json, jsonify, abort
import json
import os
import pathlib
import requests
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from pip._vendor import cachecontrol
import google.auth.transport.requests

app = Flask(__name__)
app.secret_key = "randomstring"

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "372496487601-j3b15ndne8d0372kinjc6int4ia8jjsv.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
	client_secrets_file=client_secrets_file,
	scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
	redirect_uri="http://127.0.0.1:8080/callback"
)

def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401) # Authorization required
        else:
            return function()

    return wrapper

@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
	id_token=credentials._id_token,
	request=token_request,
	audience=GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    return redirect("/signup")

@app.route('/')
def welcome():
    return render_template("welcome.html")

@app.route("/signup")
@login_is_required
def signup():
    data = json.load(open("data_source.json"))
    return render_template('signup.html', title="YCC-C2K Signup", jsondata=data["signup_details"], value=session["name"])

@app.route("/login")
def login():
	authorization_url, state = flow.authorization_url()
	session["state"] = state
	return redirect(authorization_url)

@app.route("/add", methods = ['POST', 'GET'])
# function to add to JSON
# return display_json.html with new data
# that contain
def write_json(filename='data_source.json'):
    if request.method == 'POST':
        new_data = request.form
    #return render_template('result.html', result = new_data)

    with open(filename,'r+') as file:
        # First we load existing data into a dict.
        file_data = json.load(file)
        # Join new_data with file_data inside emp_details
        file_data["signup_details"].append(new_data)
        # Sets file's current position at offset.
        file.seek(0)
        # convert back to json.
        json.dump(file_data, file, indent = 4)

        # final step: display the json with new data in html
        return render_template('signup.html', title="YCC-C2K Signup", jsondata=file_data["signup_details"], value=session["name"])

@app.route("/remove", methods = ['POST', 'GET'])
# function to add to JSON
# return display_json.html with new data
# that contain
def remove_element(filename='data_source.json'):
    if request.method == 'POST':
        remove_me = request.form
        print(remove_me['student_name'])
        print(remove_me['signup_date'])

    with open(filename,'r+') as file:
        # First we load existing data into a dict.
        file_data = json.load(file)
        # Join new_data with file_data inside emp_details

        # file_data["signup_details"] = list(filter(lambda i: i['student_name'] != "Han", file_data["signup_details"]))
        file_data["signup_details"] = list(filter(lambda i: ( (i['student_name'] != remove_me['student_name']) and (i['signup_date'] != remove_me['signup_date'])), file_data["signup_details"]))

        # print(file_data)

        # Sets file's current position at offset.
        file.seek(0)
        file.close()
        # convert back to json.
        json.dump(file_data, open(filename, 'w+'), indent = 4)

    # final step: display the json with new data in html
    return render_template('signup.html', title="DISPLAY JSON DATA IN HTML", jsondata=file_data["signup_details"], value=remove_me['student_name'])


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)