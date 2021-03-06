from typing import Union, List
import os
import glob
import random
import time
import math
import vlc


class RadioStation:
    def __init__(self, name: str, freq: float, file_name: str):
        if not os.path.exists(file_name):
            file_name = self.find_file_path(file_name)

        self.name: str = name
        self.frequency: float = freq
        self.file_name: str = file_name
        self.media: vlc.Media = vlc.Media(file_name)
        self.length: float = self._get_length()
        self.station_offset: int = random.randrange(0, self.length)

    def _get_length(self) -> float:
        """Gets the length of the radio station in ms"""
        player = vlc.MediaPlayer(self.file_name)
        player.play()
        player.set_pause(True)

        # Wait for the player to load
        max_wait = 1  # Wait a maximum of x seconds
        sleep_time = 0.001
        for i in range(max_wait * int(1 / sleep_time)):
            if player.get_length() > 0:
                break
            time.sleep(sleep_time)

        # Get the length and release the player
        length = player.get_length()
        player.release()
        return length

    @staticmethod
    def find_file_path(name) -> str:
        """Finds the file path in the music folder"""
        cwd = os.getcwd()
        music_path = os.path.join(cwd, 'music')
        files = glob.iglob(music_path + '/**/*.*', recursive=True)
        for file_path in files:
            file_name = os.path.basename(file_path)
            file_name_no_ext = os.path.splitext(file_name)[0]
            if file_name == name or file_name_no_ext == name:
                return file_path
        raise ValueError(f'No file named {name}')


class Radio:
    def __init__(self):
        self.current_freq: Union[float, None] = None
        self.stations: List[RadioStation] = []
        self.start_time_ms = time.time() * 1000
        self.current_station_name = ''
        self.equalizer = vlc.AudioEqualizer()

        # Init noise players
        self.noise_player: vlc.MediaListPlayer = vlc.MediaListPlayer()
        self.noise_player.set_playback_mode(vlc.PlaybackMode.loop)
        self._load_media(self.noise_player, vlc.Media(RadioStation.find_file_path('noise.mp3')))

        # Init music player
        self.music_player: vlc.MediaListPlayer = vlc.MediaListPlayer()
        self.music_player.set_playback_mode(vlc.PlaybackMode.loop)

    def add_station(self, station: RadioStation):
        """Adds a radio station to the radio"""
        self.stations.append(station)

    def set_frequency(self, freq: float):
        """Sets the frequency of the radio station"""
        self.current_freq = freq
        station = self._get_closest_radio_station(freq)

        if self.current_station_name != station.name:
            self._change_station(station)

        self._set_volume(station)

    def get_status(self) -> dict:
        """Returns a dict of the current status of the radio"""
        station = self._get_closest_radio_station(self.current_freq)
        return {
            "station_name": station.name,
            "station_vol": 1 if abs(self.current_freq - station.frequency) <= 0.3 else 0,
            "stations": {station.name: station.frequency for station in self.stations}
        }

    @staticmethod
    def _load_media(player: vlc.MediaListPlayer, media: vlc.Media):
        """Loads the media to the MediaListPlayer"""
        ml: vlc.MediaList = vlc.MediaList()
        ml.add_media(media)
        player.stop()
        player.set_media_list(ml)

    def _change_station(self, station: RadioStation):
        """Change the radio station that is playing"""
        self.current_station_name = station.name
        self._load_media(self.music_player, station.media)
        self.music_player.play()

        # Seek to the correct time
        time_offset = self._get_station_offset(station)
        self.music_player.get_media_player().set_time(int(time_offset))

    def _set_volume(self, station: RadioStation):
        """Set the volume of the noise and music channel"""
        frequency_distance = abs(self.current_freq - station.frequency)
        amp = self._get_media_amplification(frequency_distance)

        if amp >= 20:
            # Fully tuned into station
            self.noise_player.stop()
        else:
            if not self.noise_player.is_playing():
                self.noise_player.play()
        if amp <= -20:
            # Fully outside station bounds
            self.music_player.stop()
        else:
            if not self.music_player.is_playing():
                self.music_player.play()
                time_offset = self._get_station_offset(station)
                self.music_player.get_media_player().set_time(int(time_offset))

        # Set the volume using the equalizer
        self.equalizer.set_preamp(amp)
        self.music_player.get_media_player().set_equalizer(self.equalizer)
        self.equalizer.set_preamp(-amp)
        self.noise_player.get_media_player().set_equalizer(self.equalizer)

    @staticmethod
    def _get_media_amplification(freq_distance: float) -> float:
        """Calculate the volume of the media from -20 (silent) to +20 (max) based on the frequency distance"""
        value = -2.4 * freq_distance + 1.2
        value_capped = max(0., min(value, 1))  # Clamp value in range [0, 1]
        return value_capped * 40 - 20  # Map [0, 1] to [-20, 20]

    def _get_station_offset(self, station: RadioStation) -> float:
        """Get the station offset in ms"""
        run_time_ms = time.time() * 1000 - self.start_time_ms
        return (run_time_ms + station.station_offset) % station.length

    def _get_closest_radio_station(self, freq: float) -> RadioStation:
        """Get the radio station that is closest to the given frequency"""
        min_distance = math.inf
        radio_station = None
        for station in self.stations:
            distance = abs(station.frequency - freq)
            if distance < min_distance:
                min_distance = distance
                radio_station = station
        return radio_station


vice_city_radio = Radio()
vice_city_radio.add_station(RadioStation('Flash FM', 89.6, 'FLASH.mp3'))
vice_city_radio.add_station(RadioStation("K-Chat", 91.3, 'KCHAT.mp3'))
vice_city_radio.add_station(RadioStation("Wildstyle", 94.1, 'WILD.mp3'))
vice_city_radio.add_station(RadioStation("Espantoso", 96.4, 'ESPANT.mp3'))
vice_city_radio.add_station(RadioStation("Emotion", 98.3, 'EMOTION.mp3'))
vice_city_radio.add_station(RadioStation("VCPR", 100.7, 'VCPR.mp3'))
vice_city_radio.add_station(RadioStation("Wave", 103, 'WAVE.mp3'))
vice_city_radio.add_station(RadioStation('Fever 105', 105, 'FEVER.mp3'))
vice_city_radio.add_station(RadioStation("V-Rock", 106.8, 'VROCK.mp3'))
