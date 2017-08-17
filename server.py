from flask import Flask, request, jsonify, Response, render_template
from database.database_handler import DatabaseHandler as DH
from flask_cors import CORS, cross_origin
from time import time
import atexit

dh = DH("database/SMU-logs.db")
app = Flask(__name__)
CORS(app)
times = list()


def dictionary_has_cols(cols, dictionary):
    for col in cols:
        if not (col in dictionary):
            return False
    return True


def _execute_login(data, function):
    if "email" in data and "password" in data:
        if isinstance(data["email"], str) and isinstance(data["password"], str):
            result = function(data["email"], data["password"])
            return jsonify(result)
        else:
            return Response(status=400, response="Incorrect format")
    else:
        return Response(status=400, response="Incorrect format")


@app.route("/user-validate", methods=["POST", "OPTIONS"])
@cross_origin()
def validate_user():
    global times

    start = time()
    with app.app_context():
        if request.is_json:
            data = request.json
            if "id" in data and "pass" in data:
                if isinstance(data["id"], str) and isinstance(data["pass"], str):

                    status, msg = dh.validate_user(data["id"], data["pass"])

                    if status:
                        times.append({"path": "/user-validate", "time": time() - start})
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
    global times

    start = time()
    if request.is_json:
        data = request.get_json(force=True)
        if "id" in data and "course" in data:
            if isinstance(data["id"], str) and isinstance(data["course"], str):
                status, response = dh.start_work(data["id"], data["course"])
                if status:
                    times.append({"path": "/start-work", "time": time() - start})
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
    global times

    start = time()
    if request.is_json:
        data = request.json
        if "id" in data and "time" in data:
            if isinstance(data["id"], str) and isinstance(data["time"], int):
                status, response = dh.stop_work(data["id"], data["time"])
                if status:
                    times.append({"path": "/stop-work", "time": time() - start})
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
    global times

    start = time()
    if request.is_json:
        data = request.json
        if "email" in data and "name" in data and "password" in data and "admin" in data:
            if isinstance(data["email"], str) and isinstance(data["password"], str) and \
                isinstance(data["admin"], int) and isinstance(data["name"], str):

                status, msg = dh.add_user(data["email"], data["name"], data["password"], data["admin"] == 1)

                if status:
                    times.append({"path": "/signup", "time": time() - start})
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
    global times

    start = time()
    if request.is_json:
        data = request.json
        return _execute_login(data, dh.user_login)
    else:
        return Response(status=400, response="Incorrect format")


@app.route("/get-courses", methods=["GET", "OPTIONS"])
@cross_origin()
def get_courses():
    """
        Function that receives a GET request for the list of courses and returns it
    in a JSON of the format:

        {
            "success":  <True/ False>
            "courses": [
                {
                    "id": <id>,
                    "name": <name>
                }, ...
            ],                                  (only if successful)
            "message": <ERROR message>          (only if not successful)
        }
    :return:
    """
    global times

    start = time()
    #TODO: fix this provisionary user_id from here!!!!!!!!!!!!!!
    uid = "ecc6b34288d5c96494cd84efa927ab27023b22d59b6c4b6c412b1c9a5515e720"

    result = dh.get_courses_list(uid)

    times.append({"path": "/get-courses", "time": time() - start})
    return jsonify(result)


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
    global times

    start = time()
    if request.is_json:
        data = request.json
        if "token" in data:
            if isinstance(data["token"], str):
                result = dh.is_token_still_valid(data["token"])
                times.append({"path": "/user/valid-session", "time": time() - start})
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

    return jsonify(dh.get_working_users)


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
    global times

    start = time()
    if request.is_json:
        data = request.json
        if "id" in data and isinstance(data["id"], str):
            result = dh.logout_user(data["id"])
            times.append({"path": "/user/logout", "time": time() - start})
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
    global times

    start = time()
    if request.is_json:
        data = request.json
        if "asking" in data and "user" in data:
            if isinstance(data["asking"], str) and isinstance(data["user"], str):
                times.append({"path": "/user/stats/general", "time": time() - start})
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
    :return:    A rendered template with the user's history (if the asking user has enough rights)
    """
    global times

    start = time()
    if request.is_json:
        data = request.json
        if "asking" in data and "user" in data:
            if isinstance(data["asking"], str) and isinstance(data["user"], str):
                resp = dh.get_history_for_user(data["asking"], data["user"])
                resp["working"] = dh.user_is_working(data["user"])
                times.append({"path": "/user/stats/history", "time": time() - start})
                return render_template("html/stats/history.html", data=resp)
            else:
                return Response(status=400, response="Wrong format")
        else:
            return Response(status=400, response="Wrong format")
    else:
        return Response(status=400, response="Wrong format")


@app.route("/stats/leaderboard", methods=["GET", "OPTIONS"])
@cross_origin()
def get_leaderboard():
    global times

    start = time()
    data = dh.get_leaderboard()
    times.append({"path": "/stats/leaderboard", "time": time() - start})
    return render_template("html/stats/leaderboard.html", data=data)


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
    global times

    start = time()
    try:
        user_id = request.args.get("id")
    except:
        return Response(status=400, response="Invalid request arguments")

    data = dh.user_is_working(user_id)

    times.append({"path": "/user/is-working", "time": time() - start})
    return jsonify(data)


@app.route("/working/update-time", methods=["PUT", "OPTIONS"])
@cross_origin()
def update_time():
    """
          Function that handles a request for updating the working time for user

          Request URL has to be of the format:

                https://www.neural-guide.me/working/update-time?id=<user_id>&time=<time_in_seconds>

    :return:    A Response based on the result of the update
    """
    global times

    start = time()

    try:
        id = request.args.get("id")
        t = int(request.args.get("time"))
    except:
        return Response(status=400, response="Invalid request arguments")

    status, msg = dh.update_time(id, t)

    times.append({"path": "/working/update-time", "time": time() - start})
    if status:
        return Response(status=200, response="All good")
    else:
        return Response(status=400, response=msg)


@app.route("/courses", methods=["GET", "OPTIONS"])
@cross_origin()
def courses():
    global times

    #TODO: UPDATE THE WAY THE REQUEST IS MADE!!!!!!
    uid = "ecc6b34288d5c96494cd84efa927ab27023b22d59b6c4b6c412b1c9a5515e720"

    start = time()
    data = dh.get_courses_list_with_details(uid)
    times.append({"path": "/courses", "time": time() - start})
    print(data["courses"])
    return render_template("html/courses.html", data=data["courses"])


@app.route("/user/info", methods=["GET", "OPTIONS"])
@cross_origin()
def account_info():
    """
        Function that returns the user information for a specific user

        Expects an URL with the following format:

        https://www.neural-guide.me/user/info?id_asker=<id of the user asking for the information>&id_user<id of the user we want the information for>

    :return:    A rendered HTML template with all the required information and functionalities
    """
    global times

    start = time()

    id_asker = request.args.get("id_asker")
    id_user = request.args.get("id_user")
    data = dh.get_user_details(id_asker, id_user)

    times.append({"path": "/user/info", "time": time() - start})
    return render_template("html/user-info.html", data=data)


@app.route("/user/update/password", methods=["POST", "OPTIONS"])
@cross_origin()
def update_user_password():
    """

        Function that updates a user's password

        It also expects a JSON in the request, with the following format:

                {
                    "id_user":      <the id of the user we update the password for>
                    "id_admin":     <the id of the admin doing the update>                  (only if done by an admin)
                    "old_pass":     <the old password of the user>                          (only if done by the user)
                    "new_pass":     <the new password of the user>
                }

    :return:    A JSON with the following format:

                {
                    "success":      <True/ False>,
                    "message":      <ERROR_message>     (only if not successful)
                }
    """
    start = time()
    if request.is_json:
        data = request.json
        if dictionary_has_cols(("id_user", "id_admin", "new_pass"), data):
            times.append({"path": "/user/update/password", "time": time() - start})
            return jsonify(dh.update_user_password_as_admin(data["id_admin"], data["id_user"], data["new_pass"]))
        elif dictionary_has_cols(("id_user", "old_pass", "new_pass"), data):
            times.append({"path": "/user/update/password", "time": time() - start})
            return jsonify(dh.update_user_password(data["id_user"], data["old_pass"], data["new_pass"]))
        else:
            return Response(status="500", response="invalid JSON format")
    else:
        return Response(status="500", response="Request not a JSON")


@app.route("/user/update/name", methods=["POST", "OPTIONS"])
@cross_origin()
def update_user_name():
    """
        Function that handles a request to update a user's name

        It expects a JSON with the following format:

            {
                "id_updater": <id of the user doing the update>
                                (has to be either the same as id_user or an admin)
                "id_user":    <id of the user we update the name for>
                "new_name":   <the new name of the user>
            }
    :return:

            {
                "success":   <True/ False>
                "message":   <ERROR_message>    (only if not successful)
            }
    """
    global times

    start = time()
    if request.is_json:
        data = request.json
        if dictionary_has_cols(("id_updater", "id_user", "new_name"), data):
            times.append({"path": "/user/update/time", "time": time() - start})
            return jsonify(dh.update_user_name(data["id_updater"], data["id_user"], data["new_name"]))
        else:
            return Response(status="500", response="invalid JSON format")
    else:
        return Response(status="500", response="Request not a JSON")


@app.route("/stop-work/forced", methods=["PUT", "OPTIONS"])
@cross_origin()
def stop_work_forced():
    """
        Function that handles a forced stop_work request (i.e. without the user pressing the "Done" button on
            the working.html page)

        Expects an URL with the following format:

        https://www.neural-guide.me/stop-work/forced?id_asker=<id of the user that wants to perform the action>&
                                                     id_user=<id of the user that stops working>
    :return:
    """

    global times

    start = time()

    try:
        id_asker = request.args.get("id_asker")
        id_user = request.args.get("id_user")
    except:
        return Response(status=400, response="Incorrect parameters")

    sts, msg = dh.force_stop_work(id_asker, id_user)

    times.append({"path": "/stop-work/forced", "time": time() - start})

    if sts:
        return Response(status=200)
    else:
        return Response(status=400, response=msg)


@app.route("/admin/get-times", methods=["GET", "OPTIONS"])
@cross_origin()
def display_stats():
    global times
    result = {
        "breakdown": times,
        "total": len(times),
        "mean": sum([x["time"] for x in times])/len(times) if len(times) != 0 else 0
    }

    return jsonify(result)


if __name__ == "__main__":
    try:
        app.run(port=5000, debug=True)
    finally:
        print("This sucks")
