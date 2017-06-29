from flask_cors import CORS, cross_origin
from flask import Flask, request, jsonify

app = Flask(__name__)
CORS(app)

@app.route("/validate", methods=["POST", "OPTIONS"])
@cross_origin()
def validate():

    print("works")

    if request.is_json:
        print("here")
        data = request.json
        print(data)
        return jsonify({"email": "abc@def.com",
                        "password": "test"})
    else:
        print("not a JSON")
        return jsonify({"email": "abc@def.com",
                        "password": "test"})


if __name__ == "__main__":
    app.run(debug=True)