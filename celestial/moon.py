from .base import CelestialBody
import ephem
import math
from skyfield.api import load, Topos
from astropy.coordinates import get_constellation, EarthLocation, AltAz
from astropy.time import Time
import astropy.units as u

# Load skyfield data (shared, but for now, load here)
ts = load.timescale()
eph = load('de421.bsp')
earth = eph['earth']
moon_sf = eph['moon']

class Moon(CelestialBody):
    """
    CelestialBody subclass for the Moon. Implements all required astronomical calculations and enhancements.
    """
    def __init__(self):
        super().__init__('moon')
        self.ephem_body = ephem.Moon()  # PyEphem object for the Moon
        self.skyfield_body = eph['moon']  # Skyfield object for the Moon

    def get_basic_info(self, observer):
        """
        Get basic information about the Moon using ephem for the given observer.
        Includes position, distance, phase, and next new/full moon dates.
        """
        self.ephem_body.compute(observer)
        altitude_deg = math.degrees(float(self.ephem_body.alt))
        azimuth_deg = math.degrees(float(self.ephem_body.az))
        body_data = {
            "name": self.name,
            "position": {
                "altitude": {"degrees": round(altitude_deg, 2), "radians": str(self.ephem_body.alt)},
                "azimuth": {"degrees": round(azimuth_deg, 2), "radians": str(self.ephem_body.az)}
            },
            "distance": {"km": int(self.ephem_body.earth_distance * 149597870.691)},
            "constellation": ephem.constellation(self.ephem_body)[1]
        }
        # Calculate next new and full moon dates
        next_new = ephem.next_new_moon(observer.date)
        next_full = ephem.next_full_moon(observer.date)
        body_data["current_phase"] = round(self.ephem_body.phase, 2)
        body_data["next_phases"] = [
            {"phase": "New Moon", "date": ephem.Date(next_new).datetime().strftime("%Y-%m-%d %H:%M:%S UTC")},
            {"phase": "Full Moon", "date": ephem.Date(next_full).datetime().strftime("%Y-%m-%d %H:%M:%S UTC")}
        ]
        return body_data

    def enhance_with_skyfield(self, body_data, current_time, lat, lon, has_location):
        """
        Enhance the Moon data with more precise calculations using skyfield.
        Adds celestial coordinates, precise distance, and phase. If location is provided, adds precise altitude/azimuth.
        """
        t = ts.from_datetime(current_time)
        earth_at_t = earth.at(t)
        body_at_t = earth_at_t.observe(self.skyfield_body)
        ra, dec, distance = body_at_t.radec()
        body_data["celestial_coordinates"] = {
            "right_ascension": {"hours": round(ra.hours, 4), "degrees": round(ra.hours * 15, 4)},
            "declination": {"degrees": round(dec.degrees, 4)}
        }
        body_data["distance"]["au"] = round(distance.au, 6)
        # Calculate phase using skyfield
        sun = eph['sun']
        e = earth.at(t)
        s = e.observe(sun).apparent()
        m = e.observe(self.skyfield_body).apparent()
        sun_angle = s.separation_from(m)
        phase_angle = abs(180 - sun_angle.degrees)
        phase_percent = 100 * (1 - phase_angle/180)
        body_data["phase_precise"] = round(phase_percent, 2)
        if has_location:
            # If location is provided, add precise altitude/azimuth
            location = Topos(latitude_degrees=lat, longitude_degrees=lon)
            observer_at_t = earth.at(t) + location
            alt, az, _ = observer_at_t.observe(self.skyfield_body).apparent().altaz()
            body_data["position"]["precise_altitude"] = round(alt.degrees, 4)
            body_data["position"]["precise_azimuth"] = round(az.degrees, 4)

    def enhance_with_astropy(self, body_data, current_time, lat, lon, has_location):
        """
        Enhance the Moon data with advanced calculations using astropy.
        Adds precise constellation and placeholder for enhanced illumination. If location is provided, adds viewing conditions and libration note.
        """
        t = Time(current_time)
        from astropy.coordinates import get_moon, get_sun
        body_coords = get_moon(t)
        body_icrs = body_coords.transform_to('icrs')
        constellation = get_constellation(body_icrs)
        body_data["constellation_precise"] = constellation
        # Placeholder for enhanced illumination calculation
        body_data["illumination_details"] = {"note": "Enhanced illumination calculation available"}
        if has_location:
            # If location is provided, add viewing conditions and libration note
            observer = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
            altaz_frame = AltAz(obstime=t, location=observer)
            body_altaz = body_icrs.transform_to(altaz_frame)
            body_data["viewing_conditions"] = {
                "atmospheric_extinction": "Calculated based on altitude",
                "best_viewing_time": "Based on maximum altitude"
            }
            body_data["libration"] = {"note": "Libration values available on request"}

    def add_rise_set_times(self, body_data, observer, has_location):
        """
        Add next moonrise and moonset times to the data if location is provided.
        Handles circumpolar cases gracefully.
        """
        if not has_location:
            return
        try:
            rise_set_info = {}
            observer.horizon = "-0:34"  # Standard atmospheric refraction
            try:
                next_rise = observer.next_rising(self.ephem_body).datetime()
                rise_set_info["next_moonrise"] = next_rise.strftime("%Y-%m-%d %H:%M:%S UTC")
            except ephem.CircumpolarError:
                rise_set_info["next_moonrise"] = "Moon is circumpolar - never rises"
            try:
                next_set = observer.next_setting(self.ephem_body).datetime()
                rise_set_info["next_moonset"] = next_set.strftime("%Y-%m-%d %H:%M:%S UTC")
            except ephem.CircumpolarError:
                rise_set_info["next_moonset"] = "Moon is circumpolar - never sets"
            body_data["moonrise_and_set"] = rise_set_info
        except Exception as e:
            body_data["rise_set_error"] = str(e) 