from flask import Flask, request, jsonify, Response, render_template
from database.database_handler import DatabaseHandler as DH
from flask_cors import CORS, cross_origin

dh = DH("database/SMU-logs.db")
app = Flask(__name__)
CORS(app)


@app.route("/user-validate", methods=["POST", "OPTIONS"])
@cross_origin()
def validate_user():
    with app.app_context():
        if request.is_json:
            data = request.json
            if "id" in data and "pass" in data:
                if isinstance(data["id"], str) and isinstance(data["pass"], str):

                    status, msg = dh.validate_user(data["id"], data["pass"])

                    if status:
                        return Response(status=200, response="Success")
                    elif msg != "Server error":
                        return Response(status=400, response=msg)
                    else:
                        return Response(status=500, response="Server error")
                else:
                    return Response(status=400, response="Wrong request")
            else:
                return Response(status=400, response="Wrong request")
        else:
            return Response(status=400, response="Wrong request")


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
                print(data["token"], result)
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


@app.route("/user/stats/general", methods=["POST", "OPTIONS"])
@cross_origin()
def user_stats():
    """
        Method that handles a request for user statistics.

        It expects a POST request containing a JSON with the following format:

            {
                "asking": <id_of_the_user_asking_for_the_data>,
                "user": <id_of_the_user_we_ask_for>
            }
    :return:
        A JSON of the format:

            {
                "success": <True/ False>,
                "seconds": <no_of_seconds_worked>,      (only if successful)
                "message": <ERROR_message>              (only if not successful)
            }
    """
    if request.is_json:
        data = request.json
        if "asking" in data and "user" in data:
            if isinstance(data["asking"], str) and isinstance(data["user"], str):
                return jsonify(dh.get_stats_for_user(data["asking"], data["user"]))
            else:
                return Response(status=400, response="Wrong format")
        else:
            return Response(status=400, response="Wrong format")
    else:
        return Response(status=400, response="Wrong format")


@app.route("/user/stats/history", methods=["POST", "OPTIONS"])
@cross_origin()
def user_history():
    """
        Method that handles a request for user statistics.

        It expects a POST request containing a JSON with the following format:

            {
                "asking": <id_of_the_user_asking_for_the_data>,
                "user": <id_of_the_user_we_ask_for>
            }
    :return:
                        {
                            "success": <True/False>,
                            "history": [                                        (only if successful)
                                {
                                    "id": <entry_id>,
                                    "course_name": <Course_name>,
                                    "cour"se_url": <course_url>,
                                    "started_at": <started_at>,
                                    "logged_at": <time_entry_was_logged>,
                                    "seconds":  <no_of_seconds_spent_working>
                                },
                                { ... },
                                ...
                            ],
                            "message": <ERROR_message>                          (only if not successful)
                        }
    """
    if request.is_json:
        data = request.json
        if "asking" in data and "user" in data:
            if isinstance(data["asking"], str) and isinstance(data["user"], str):
                return jsonify(dh.get_history_for_user(data["asking"], data["user"]))
            else:
                return Response(status=400, response="Wrong format")
        else:
            return Response(status=400, response="Wrong format")
    else:
        return Response(status=400, response="Wrong format")


@app.route("/stats/leaderboard", methods=["GET", "OPTIONS"])
@cross_origin()
def get_leaderboard():
    return jsonify(dh.get_leaderboard())


@app.route("/user/is-working", methods=["GET", "OPTIONS"])
@cross_origin()
def is_working():
    """
          Function that handles a request for getting information about what a user is currently working on

          The request URL has to have the format:

                https://www.neural-guide.me/user/is-working?id=<user_id>

    :return:        A JSON of the format:

                {
                    "success": <True/ False>,
                    "working": <True/ False>,       (only if successful)
                    "course": <course_name>,        (only if successful and working)
                    "time": <no_of_seconds_working> (only if successful and working)
                    "message": <ERROR_message>      (only if not successful)
                }
    """
    try:
        user_id = request.args.get("id")
    except:
        return Response(status=400, response="Invalid request arguments")

    return jsonify(dh.user_is_working(user_id))


@app.route("/working/update-time", methods=["PUT", "OPTIONS"])
@cross_origin()
def update_time():
    """
          Function that handles a request for updating the working time for user

          Request URL has to be of the format:

                https://www.neural-guide.me/working/update-time?id=<user_id>&time<time_in_seconds>

    :return:    A Response based on the result of the update
    """
    try:
        id = request.args.get("id")
        time = int(request.args.get("time"))
    except:
        return Response(status=400, response="Invalid request arguments")

    status, msg = dh.update_time(id, time)

    if status:
        return Response(status=200, response="All good")
    else:
        return Response(status=400, response=msg)


@app.route("/courses", methods=["GET", "OPTIONS"])
@cross_origin()
def courses():
    data = dh.get_courses_list_with_details()
    return render_template("html/courses.html", data=data["courses"])


@app.route("/leaderboard", methods=["GET", "OPTIONS"])
@cross_origin()
def leaderboard():
    data = dh.get_leaderboard()
    print(data["leader_board"])
    return render_template("html/stats/leaderboard.html", data=data["leader_board"])

if __name__ == "__main__":
    app.run(port=5000, debug=True)
