import requests
from flask import Flask, render_template
from flask_cors import CORS, cross_origin
import pandas as pd

app = Flask(__name__)
CORS(app)


@app.route("/stats", methods=["GET", "OPTIONS"])
@cross_origin()
def get_stats():
    try:
        r = requests.get("https://www.neural-guide.me/admin/get-times")
        data = r.json()
    except:
        data = {
            "total": 0,
            "mean": 0.0,
            "breakdown": list()
        }
    data["max"] = max([x["time"] for x in data["breakdown"]]) if len(data["breakdown"]) else 0.0
    data["min"] = min([x["time"] for x in data["breakdown"]]) if len(data["breakdown"]) else 0.0
    return render_template("html/stats.html", data=data)


@app.route("/log-stats", methods=["GET"])
@cross_origin()
def write_stats():

        r = requests.get("https://www.neural-guide.me/admin/get-times")
        data = r.json()
        cols = ["path", "name"]
        df = pd.DataFrame(columns=cols)
        for item in data["breakdown"]:
            new_df = pd.DataFrame([[item["path"], item["time"]]], columns=cols)
            df = df.append(new_df)

        pd.DataFrame.to_csv(df, "stats1.csv")
        return "SUCCESS"

if __name__ == "__main__":
    app.run(port=5000, debug=True)

