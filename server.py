from flask import Flask, request, jsonify, Response
from database.database_handler import DatabaseHandler as DH
from flask_cors import CORS, cross_origin

dh = DH("database/SMU-logs.db")
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


@app.route("/start-work", methods=["POST", "OPTIONS"])
@cross_origin()
def start_work():
    """

        Method that handles a start-work request coming from the client.
        It expects a JSON of the format:

            {
                "id": <email_hash>,
                "course": <course_name>
            }

    :return:    A Response to the given request
    """
    if request.is_json:
        data = request.get_json(force=True)
        if "id" in data and "course" in data:
            if isinstance(data["id"], str) and isinstance(data["course"], str):
                status, response = dh.start_work(data["id"], data["course"])
                if status:
                    return Response(response="All good!",
                                    status=200)
                else:
                    if response == "Server error":
                        return Response(response="Server error",
                                        status=500)
                    else:
                        return Response(response=response,
                                        status=400)
            else:
                return Response(response="Wrong format",
                                status=400)
        else:
            return Response(response="Wrong format",
                            status=400)
    else:
        return Response(response="Wrong format",
                        status=400)


@app.route("/stop-work", methods=["POST", "OPTIONS"])
@cross_origin()
def stop_work():

    """
        Method that handles a stop-work request from the client
        It expects a request of the format:

            {
                "id": <email_hash>,
                "time": <time>
            }



    :return:
    """

    if request.is_json:
        data = request.json
        if "id" in data and "time" in data:
            if isinstance(data["id"], str) and isinstance(data["time"], int):
                status, response = dh.stop_work(data["id"], data["time"])
                if status:
                    return Response(response="All good!",
                                    status=200)
                else:
                    if response == "Server error":
                        return Response(response="Server error",
                                        status=500)
                    else:
                        return Response(response=response,
                                        status=400)
            else:
                return Response(response="Wrong format",
                                status=400)
        else:
            return Response(response="Wrong format",
                            status=400)
    else:
        return Response(response="Wrong format",
                        status=400)


@app.route("/user/signup", methods=["POST", "OPTIONS"])
@cross_origin()
def signup():
    """
           Method that handles a signup request from the client
           It expects a request of the format:

               {
                   "email": <email>,
                   "name": <name>,
                   "password": <password>,
                   "admin": 0 - if not
                            1 - if yes
               }

    :return:
    """
    if request.is_json:
        data = request.json
        if "email" in data and "name" in data and "password" in data and "admin" in data:
            if isinstance(data["email"], str) and isinstance(data["password"], str) and \
                isinstance(data["admin"], int) and isinstance(data["name"], str):

                status, msg = dh.add_user(data["email"], data["name"], data["password"], data["admin"] == 1)

                if status:
                    return Response(200, "Success")
                else:
                    if msg != "Server error":
                        return Response(400, msg)
                    else:
                        return Response(500, msg)
            else:
                return Response(400, "Incorrect format")
        else:
            return Response(400, "Incorrect format")
    else:
        return Response(400, "Incorrect format")


@app.route("/user/login", methods=["POST", "OPTIONS"])
@cross_origin()
def login():
    """
             Method that handles a signup request from the client
             It expects a request of the format:

                 {
                     "email": <hashed_email>,
                     "password": <password>,
                 }

      :return:
            A JSON of the format:
                {
                    "success": <True/ False>,
                    "id": <user_id>,              (only if successful or user not validated)
                    "name": <user's_full_name>   (only if successful)
                    "token": <login_token>,      (only if successful)
                    "ttl":   <TTL>,              (only if successful)
                    "message":  <error_message>  (only if not successful)
                }
      """
    if request.is_json:
        data = request.json
        if "email" in data and "password" in data:
            if isinstance(data["email"], str) and isinstance(data["password"], str):
                result = dh.verify_user(data["email"], data["password"])
                return jsonify(result)
            else:
                return Response(status=400, response="Incorrect format")
        else:
            return Response(status=400, response="Incorrect format")
    else:
        return Response(status=400, response="Incorrect format")


@app.route("/get-courses", methods=["GET", "OPTIONS"])
@cross_origin()
def get_courses():
    """
        Function that receives a GET request for the list of courses and returns it
    in a JSON of the format:

        {
            "courses": [
                {
                    "id": <id>,
                    "name": <name>
                }, ...
            ]
        }
    :return:
    """
    status, courses = dh.get_courses_list()

    if not status:
        return Response(status=500, response="Server error")
    else:
        return jsonify(courses)


@app.route("/user-validate", methods=["POST", "OPTIONS"])
@cross_origin()
def validate_user():

    with app.test_request_context():
        if request.is_json:
            data = request.json
            if "id" in data and "pass" in data:
                if isinstance(data["id"], str) and isinstance(data["pass"], str):

                    status, msg = dh.validate_user(data["id"], data["pass"])

                    if status:
                        return Response(200, "Success")
                    elif msg != "Server error":
                        return Response(400, msg)
                    else:
                        return Response(500, "Server error")
                else:
                    return Response(400, "Wrong request")
            else:
                return Response(400, "Wrong request")
        else:
            return Response(400, "Wrong request")


@app.route("/user/valid-session", methods=["POST", "OPTIONS"])
@cross_origin()
def check_session():
    """
        Method that checks whether the login session from the user is still valid or not, based on a token

        Expects a JSON of the format:
            {
                "token": <token>
            }

    :return:
        A  JSON of the format:

            {
                "success": <True/ False>,
                "valid":   <True/ False>,       (only if successful)
                "message": <Error message>      (only if not successful)
            }
    """
    if request.is_json:
        data = request.json
        if "token" in data:
            if isinstance(data["token"], str):
                result = dh.is_token_still_valid(data["token"])
                return jsonify(result)
            else:
                return Response(400, "Invalid format")
        else:
            return Response(400, "Invalid format")
    else:
        return Response(400, "Invalid format")


@app.route("/working-users", methods=["GET", "OPTIONS"])
@cross_origin()
def working_users():

    return jsonify(dh.get_working_users())


@app.route("/logs", methods=["GET", "OPTIONS"])
@cross_origin()
def get_logs():
    return jsonify(dh.get_logs())


@app.route("/user/logout", methods=["POST", "OPTIONS"])
@cross_origin()
def logout():
    """
        Method that handles a logout request coming from the user

        Expects a JSON of the format:

            {
                "id": <user_id>
            }

    :return:    a JSON of the format:

            {
                "success": <True/False>,
                "message": <ERROR_message>      (only if not successful)
            }

    """
    if request.is_json:
        data = request.json
        if "id" in data and isinstance(data["id"], str):
            result = dh.logout_user(data["id"])
            return jsonify(result)
        else:
            return Response(status=400, response="Wrong request format")
    else:
        return Response(status=400, response="Wrong request format")

if __name__ == "__main__":
    app.run(port=5000, debug=True)
