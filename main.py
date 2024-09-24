from flask import Flask, request, jsonify, make_response, render_template, send_from_directory, redirect
import db
from flask.templating import render_template
from werkzeug.utils import secure_filename
import jwt
import datetime
import json
import os
import uuid
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
from bson import json_util


app = Flask(__name__)
app.config['SECRET_KEY'] = "kdfjld"


@app.route("/login")
def hello_world():
    
    return render_template('Login_SignUp_page.html')


@app.route("/")
def main_file():
    token = request.cookies.get('JWT_TOKEN')
    if token is None:
        return redirect("/login")
    return render_template('filter_college.html')

@app.route("/chat")
def chat():
    token = request.cookies.get('JWT_TOKEN')
    if token is None:
        return redirect("/login")
    return render_template('chat_bot.html')

@app.route("/recommendations")
def recommendations():
    token = request.cookies.get('JWT_TOKEN')
    if token is None:
        return redirect("/login")
    return render_template('recommendations.html')


@app.route("/api/createUser", methods=["POST"])
def createUser():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data or len(data['username']) == 0 or len(
            data["password"]) == 0:
        return jsonify({"message": "Missing username or password"}), 400
    print(len(data["username"]))
    username = data["username"]
    password = data["password"]
    accountID = str(uuid.uuid4())

    if db.find_user_by_username(username):
        return jsonify({"message": "User already exists"}), 401

    db.add_document("users", {"username": username, "password": password, "likes": [], "dislikes": []})
    return jsonify({"message": "User created successfully"}), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or "username" not in data or "password" not in data:
        return jsonify({"message": "Missing username or password"}), 401

    username = data["username"]
    password = data["password"]

    if not data or not db.login_successful(username, password):
        return jsonify({"message": "Invalid username or password"}), 401

    userID = db.find_user_by_username(username)["_id"]
    data = {
        "username": username,
        "userID": str(userID),
        "expiration": str(datetime.datetime.now() + datetime.timedelta(hours=24))
    }
    token = jwt.encode(data, str(app.config["SECRET_KEY"]), algorithm="HS256")

    # Set the JWT token as a cookie
    response = make_response(jsonify({"message": "Login Successful"}), 200)
    expiration_time = datetime.datetime.now() + datetime.timedelta(days=1)
    expires_formatted = expiration_time.strftime("%a, %d %b %Y %H:%M:%S GMT")
    response.set_cookie("JWT_TOKEN", token, httponly=True, secure=True, samesite="Strict", max_age=24 * 60 * 60,
                        expires=expires_formatted)

    return response

@app.route("/api/getRandomArticle", methods=["GET"])
def getRandomArticle():
    article = db.find_random_document()
    article.pop("vector")
    return json.loads(json_util.dumps(article))

@app.route("/api/addLiked", methods=["POST"])
def addLiked():
    data = request.get_json()

    if not data or "articleID" not in data:
        return jsonify({"message": "Missing articleID"}), 400

    article_id = data["articleID"]

    token = request.cookies.get("JWT_TOKEN")
    if not token:
        return jsonify({"message": "unauthenticated token"}, 403)

    try:
        # Decode the JWT token
        decoded_data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        user_id = decoded_data["userID"]  # Extract userID from the token
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 403

    if article_id not in db.get_account_from_id(user_id)["likes"]:
        db.update_user_likes(db.get_account_from_id(user_id)["username"], article_id)

    return jsonify({"message": "Article liked successfully"}), 200


@app.route("/api/addDisliked", methods = ["POST"])
def addDisliked():
    data = request.get_json()
    if not data or "articleID" not in data:
        return jsonify({"message": "Missing username or articleID"}, 400)

    article_id = data["articleID"]

    token = request.cookies.get("JWT_TOKEN")

    if not token:
        return jsonify({"message": "unauthenticated token"}, 403)

    try:
        # Decode the JWT token
        decoded_data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        user_id = decoded_data["userID"]  # Extract userID from the token
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 403

    if article_id not in db.get_account_from_id(user_id)["dislikes"]:
        db.update_user_dislikes(db.get_account_from_id(user_id)["username"], article_id)

    return jsonify({"message": "dislike added successfuly"}, 200)


@app.route("/api/Recs", methods=["GET"])
def getRecs():
    token = request.cookies.get("JWT_TOKEN")

    if not token:
        return jsonify({"message": "Not authenticated"}), 403

    try:
        # Decode the JWT token
        decoded_data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        user_id = decoded_data["userID"]  # Extract userID from the token
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 403
    # Get recommendations
    recommendations = db.get_articles_you_may_like(user_id, 10)

    if recommendations is None or len(recommendations) == 0:
        return jsonify({"message": "No recommendations found. Add some recommendations."}), 404

    return json.loads(json_util.dumps(recommendations))

@app.route("/api/llmReq",  methods = ["POST"])
def llmReq():
    data = request.get_json()
    if "message_history" not in data or "query" not in data:
        return jsonify({"message": "Missing message history or query"}, 400)
    
    return db.llm_response(data["query"], message_history=data["message_history"])


if __name__ == "__main__":
    app.run(debug=True, port = 5000)