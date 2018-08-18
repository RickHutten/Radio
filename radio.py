from random import random
from threading import Lock
import time
import subprocess
import os

_lock = Lock()

_radio_start = time.time()  # Save the time the radio was started

_noise = './noise.mp3'

_emotion = './Vice\ City/Emotion\ 98.3.mp3'
_fever = './Vice\ City/Fever\ 105.mp3'
_flash = './Vice\ City/Flash\ FM.mp3'
_k_chat = './Vice\ City/K-Chat.mp3'
_espantoso = './Vice\ City/Radio\ Espantoso.mp3'
_vcpr = './Vice\ City/Vice\ City\ Public\ Radio.mp3'
_v_rock = './Vice\ City/V-Rock.mp3'
_wave = './Vice\ City/Wave\ 103.mp3'
_wildstyle = './Vice\ City/Wildstyle.mp3'
_dash_1580 = 'http://198.255.26.61/DASH11?cb=1533205004'

_noise_pipe = '/home/pi/Programs/Radio/chan1'
_station_pipe = '/home/pi/Programs/Radio/chan2'

_stations = [_flash, _k_chat, _dash_1580, _wildstyle, _espantoso, _emotion, _vcpr, _wave, _fever, _v_rock]
_frequencies = [89.6, 91.3, 93.1, 94.9, 96.4, 98.3, 100.7, 103, 105, 106.8]
_durations = [3783.8, 6236.4, 0, 4106.4, 3698.7, 3547.0, 5185.2, 3966.6, 3794.1, 4642.2]
_start_pos = [random() * 10000 for _ in _stations]  # Start position of radio at start of program

_internet_radio = [_dash_1580]  # List the radio stations that are actual internet radios

_station_fade = 0.5  # Where the station can be heard with noise
_station_width = 0.1  # How big the tolerance is without hearing noise
_min_dist = (_station_fade * 2 + _station_width) + 0.1  # Minumum distance _stations should be separated

_current_frequency = 0  # The frequency that is currently set
_current_station = ""
_frequency_error = 0.05  # Allowed error in frequency change before adjusting volume/channels


def _check_station_distance():
    """
    Check if the radio stations are seperated enough. Warn the user if not.
    :return: -
    """
    for i, freq in enumerate(_frequencies):
        if i == 0:
            continue
        station_distance = freq - _frequencies[i - 1]
        if station_distance < _min_dist:
            print 'Warning: Station distance too low between', _frequencies[i - 1], 'and', freq


def _get_station(frequency):
    """
    Gets the station which is closest together with the respective noise
    and station volume
    :param frequency: the frequency the radio is tuned to
    :return: data = {'station_path': './...', 'station_vol': x, 'noise_vol': 100-x}
    """
    global _stations, _frequencies
    data = {}  # Data to return

    # Determine closest station
    distance_min = 100
    for i, freq in enumerate(_frequencies):
        dist = abs(frequency - freq)
        if dist < distance_min:
            distance_min = dist
            data['station_path'] = _stations[i]

    # Determine volume
    if distance_min < _station_width / 2:
        volume = 100
    elif distance_min < _station_width / 2 + _station_fade:
        volume = 100 * (1 - (distance_min - _station_width / 2) / _station_fade)
    else:
        volume = 0

    # Save volumes in return data
    data['station_vol'] = int(round(volume))
    data['noise_vol'] = int(round(100 - volume))

    return data


def _get_station_offset(info):
    """
    Get the offset the station should be at given the current time and _start_pos
    :param info: {'station_path': './...', 'station_vol': x, 'noise_vol': 100-x}
    :return: float, time in seconds the station is offset
    """
    index = _stations.index(info["station_path"])
    offset = (time.time() - _radio_start) + _start_pos[index] % _durations[index]
    # print "Offset for", info["station_path"].split("/")[-1], "is", offset
    return offset


def _change_stations(info):
    """
    Change the channels of the radio
    :param info: {'station_path': './...', 'station_vol': x, 'noise_vol': 100-x}
    :return: -
    """
    if _current_station != "":
        # Stop playing the station if there was anything running
        print "Quit mplayer, current station:", _current_station, "current frequency", _current_frequency
        os.system('echo "quit" > {}'.format(_station_pipe))

        # Check if quitting was successfull, which is not guaranteed
        result = subprocess.check_output(["ps -eaf | grep mplayer"], shell=True).split("\n")
        ans = [i.split() for i in result if "grep mplayer" not in i and "noise.mp3" not in i and i.split() != []]
        if len(ans) > 0:
            print "Still running processes:", len(ans)
            for process in ans:
                print process
                print "KILLING:", "kill -9 " + process[1]
                os.system("kill -9 " + process[1])

    print "Start playing ", info["station_path"]
    if info["station_path"] in _internet_radio:
        # If internet radio, dont seek to a certain time
        os.system('mplayer -af volume=-200 -softvol -slave -input file={} {} </dev/null >/dev/null 2>&1 &'.format(_station_pipe, info["station_path"]))
    else:
        # Play in repeat
        os.system('mplayer -af volume=-200 -softvol -loop 0 -slave -input file={} {} </dev/null >/dev/null 2>&1 &'.format(
            _station_pipe, info["station_path"]))
        # Set position of the track
        offset = _get_station_offset(info)
        os.system('echo "seek {} type=2" > {}'.format(offset, _station_pipe))


def _set_volume(info):
    """
    Sets the volume of both the noise and radio track
    :param info: {'station_path': './...', 'station_vol': x, 'noise_vol': 100-x}
    :return: -
    """
    os.system('echo "volume {} 1" > {}'.format(str(info['station_vol']), _station_pipe))  # Set volume of the station
    os.system('echo "volume {} 1" > {}'.format(str(info['noise_vol']), _noise_pipe))  # Set volume of the noise


def set_frequency(frequency):
    """
    Set the frequency of the radio, volume and station
    :param frequency: the frequency to set the radio to
    :return: -
    """
    _lock.acquire()  # Acquire lock so only one thread can execure this function at a time

    try:
        print "Setting frequency to", frequency,
        global _current_frequency, _current_station

        # If change of frequency is too small, do nothing
        if _current_frequency - _frequency_error < frequency < _current_frequency + _frequency_error:
            return

        station_info = _get_station(frequency)  # Get the info of the station to play and the volume

        if station_info["station_vol"] != 0:
            print station_info["station_path"].split("/")[-1], "volume:", station_info["station_vol"]
        else:
            print ""
        if _current_station == station_info['station_path']:
            # No change in station, only adjust volume.
            _set_volume(station_info)
        else:
            # Change station and adjust volume
            _change_stations(station_info)
            _set_volume(station_info)

        # Save current station and frequency
        _current_station = station_info['station_path']
        _current_frequency = frequency

        return station_info
    finally:
        # Release lock for next process
        _lock.release()


def _init():
    """
    Initialise the radio.
    :return: -
    """
    # Warn the user if station distance is too close
    _check_station_distance()

    # Run the noise audio file, but put it on mute (-200dB) #
    os.system('mplayer -af volume=-200 -softvol -loop 0 -slave -input file={} {} </dev/null >/dev/null 2>&1 &'.format(_noise_pipe, _noise))
    os.system('echo "volume 0 1" > {}'.format(_noise_pipe))  # Set volume of the noise


_init()

if __name__ == '__main__':
    # Fake radio input
    import numpy as np

    set_frequency(105)
    time.sleep(5)
    for i in np.arange(105, 106.8 + 0.1, 0.025):
        set_frequency(i)
        time.sleep(0.1)
    time.sleep(5)
    for i in np.arange(106.8, 105 - 0.1, -0.025):
        set_frequency(i)
        time.sleep(0.1)
    time.sleep(10)
