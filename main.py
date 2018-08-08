import flask
from flask import Flask, render_template
import radio

app = Flask(__name__)


@app.route('/')
@app.route('/<freq>')
def home(freq=None):
    try:
        freq = float(freq)
        if not 85 <= freq <= 108:
            raise ValueError()
        info = radio.set_frequency(freq)
        return flask.jsonify(**info)
    except:
        return render_template("home.html"), 200


app.run(host='0.0.0.0', port=80, debug=False, threaded=True)
