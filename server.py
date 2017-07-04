from flask import Flask, request, jsonify, Response
from database.database_handler import DatabaseHandler as DH
from flask_cors import CORS, cross_origin

dh = DH("database/tests/SMU-logs.db")
app = Flask(__name__)
CORS(app)


@app.route("/start-work", methods=["POST", "OPTIONS"])
@cross_origin()
def start_work():
    """

        Method that handles a start-work request coming from the client.
        It expects a JSON of the format:

            {
                "email": <email>,
                "course": <course_name>
            }

    :return:    A Response to the given request
    """
    if request.is_json:
        data = request.get_json(force=True)
        if "email" in data and "course" in data:
            if isinstance(data["email"], str) and isinstance(data["course"], str):
                status, response = dh.start_work(data["email"], data["course"])
                if status:
                    return Response(response="All good!",
                                    status=200)
                else:
                    if response == "Server error":
                        return Response(response="Server error",
                                        status=500)
                    if response == "Incorrect email!":
                        return Response(response="Wrong email",
                                        status=400)
                    if response == "Incorrect course name":
                        return Response(response="Incorrect course name",
                                        status=400)
                    if response == "Email already in use!":
                        return Response(response="Email already in use!",
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
                "email": <email>,
                "time": <time>
            }

    :return:
    """

    if request.is_json:
        data = request.json
        if "email" in data and "time" in data:
            if isinstance(data["email"], str) and isinstance(data["time"], int):
                status, response = dh.stop_work(data["email"], data["time"])
                if status:
                    return Response(response="All good!",
                                    status=200)
                else:
                    if response == "Server error":
                        return Response(response="Server error",
                                        status=500)
                    if response == "Wrong email!":
                        return Response(response="Wrong email",
                                        status=400)
                    if response == "Incorrect time":
                        return Response(response="Incorrect time",
                                        status=400)
                    if response == "Not working":
                        return Response(response="Not working",
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


@app.route("/signup", methods=["POST", "OPTIONS"])
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


@app.route("/signup", methods=["POST", "OPTIONS"])
@cross_origin()
def login():
    """
             Method that handles a signup request from the client
             It expects a request of the format:

                 {
                     "email": <email>,
                     "password": <password>,
                 }

      :return:
      """
    if request.is_json:
        data = request.json
        if "email" in data and "password" in data:
            if isinstance(data["email"], str) and isinstance(data["password"], str):
                status, msg = dh.verify_user(data["email"], data["password"])
                if status:
                    return Response(200, "Success")
                else:
                    if msg == "Server error":
                        return Response(500, msg)
                    else:
                        return Response(400, msg)
            else:
                return Response(400, "Incorrect format")
        else:
            return Response(400, "Incorrect format")
    else:
        return Response(400, "Incorrect format")


if __name__ == "__main__":
    app.run(debug=True)