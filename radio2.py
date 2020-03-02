from typing import Union, List
import random
import time
import math
import vlc


class RadioStation:
    def __init__(self, name: str, freq: float, file_name: str):
        self.name: str = name
        self.frequency: float = freq
        self.file_name: str = file_name
        self.media = vlc.Media(self.file_name)
        self.length = self._get_length()
        self.station_offset = random.randrange(0, self.length)

    def _get_length(self) -> float:
        """Gets the length of the radio station in ms"""
        print(self.file_name)
        player = vlc.MediaPlayer(self.file_name)
        player.play()
        player.set_pause(True)

        # Wait for the player to load
        for i in range(1000):
            if player.get_length() > 0:
                break
            time.sleep(0.001)

        # Get the length and release the player
        length = player.get_length()
        player.release()
        return length


class Radio:
    def __init__(self):
        self.current_freq: Union[float, None] = None
        self.stations: List[RadioStation] = []
        self.is_initialised: bool = False
        self.start_time_ms = time.time() * 1000
        self.current_station_name = ''
        self.noise_player: vlc.MediaPlayer = vlc.MediaPlayer(r'C:\Users\rick\PycharmProjects\Radio\music\noise.mp3')
        self.music_player: vlc.MediaPlayer = vlc.MediaPlayer()
        self.equalizer = vlc.AudioEqualizer()

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
        return {
            "station_name": station.name,
            "station_vol": 1 if abs(self.current_freq - station.frequency) <= 0.3 else 0
        }

    def _change_station(self, station: RadioStation):
        """Change the radio station that is playing"""
        self.current_station_name = station.name
        self.music_player.set_media(station.media)
        self.music_player.play()

        # Seek to the correct time
        time_offset = self._get_station_offset(station)
        self.music_player.set_time(int(time_offset))

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
                self.music_player.set_time(int(time_offset))

        # Set the volume
        self.equalizer.set_preamp(amp)
        self.music_player.set_equalizer(self.equalizer)
        self.equalizer.set_preamp(-amp)
        self.noise_player.set_equalizer(self.equalizer)

    @staticmethod
    def _get_media_amplification(freq_distance: float) -> float:
        """Calculate the volume of the media from -20 (silent) to +20 (max) based on the frequency distance"""
        value = -2.4 * freq_distance + 1.2
        return max(0, min(value, 1)) * 40 - 20

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
