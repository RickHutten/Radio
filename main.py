# Set the cwd to this directory
import os
current_file_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_file_dir)

from flask import Flask, render_template, jsonify
from radio import vice_city_radio

app = Flask(__name__)


@app.route('/')
@app.route('/<float:freq>')
@app.route('/<int:freq>')
def home(freq=None):
    if freq is None:
        return render_template("home.html"), 200

    # Set the frequency of the radio
    freq = float(freq)
    if not 85 <= freq <= 108:
        print("Bad frequency:", freq)
    else:
        vice_city_radio.set_frequency(freq)

    return jsonify(**vice_city_radio.get_status())


app.run(host='0.0.0.0', port=80, debug=False, threaded=True)
