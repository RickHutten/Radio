import flask
from flask import Flask, render_template
from radio2 import Radio, RadioStation

app = Flask(__name__)

radio = Radio()
radio.add_station(RadioStation('Fever 105', 105, r'C:\Users\rick\PycharmProjects\Radio\music\radio_stations\fever_105.mp3'))
radio.add_station(RadioStation('Flash FM', 89.6, r'C:\Users\rick\PycharmProjects\Radio\music\radio_stations\flash_fm.mp3'))

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
