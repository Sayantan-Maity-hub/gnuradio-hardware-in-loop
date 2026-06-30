from flask import Flask, Response, render_template
from registry import get_nodes
import json

app = Flask(__name__)

@app.route("/")

def dashboard():
    return render_template("dashboard.html")
@app.route("/status/nodes")

def status_nodes():
    return Response(json.dumps(get_nodes(), indent = 4), mimetype="application/json")

def start_flask():
    app.run(host="0.0.0.0", port=5678, debug=False, use_reloader = False)

