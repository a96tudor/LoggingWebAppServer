from flask import Flask, request, jsonify, Response
from database.database_handler import DatabaseHandler as DH

dh = DH("database/SMU-logs.db")
app = Flask(__name__)


@app.route("/start-work", methods=["POST"])
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
        data = request.json
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
                    if response == "Incorrect email":
                        return Response(response="Wrong email",
                                        status=400)
                    if response == "Incorrect course name":
                        return Response(response="Incorrect course name",
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


@app.route("/stop-work", methods=["POST"])
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
                    if response == "Wrong email":
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


if __name__ == "__main__":
    app.run(debug=True)