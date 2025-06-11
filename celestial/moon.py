from .base import CelestialBody
import ephem
import math
from datetime import datetime
from typing import Dict, Any, Optional
import numpy as np

from astropy.coordinates import get_constellation, EarthLocation, AltAz, get_moon, get_sun
from astropy.time import Time
import astropy.units as u

from . import utils

# Load skyfield data (shared, but for now, load here)
ts = utils.load.timescale()
eph = utils.load('de421.bsp')
earth = eph['earth']
moon_sf = eph['moon']

class Moon(CelestialBody):
    """
    CelestialBody subclass for the Moon. Implements all required astronomical calculations and enhancements.
    Includes topocentric corrections, time scale handling, and nutation/aberration corrections.
    """
    def __init__(self):
        super().__init__('moon')
        self.ephem_body = ephem.Moon()  # PyEphem object for the Moon
        self.skyfield_body = utils.moon  # Skyfield object for the Moon

    def get_basic_info(self, observer) -> Dict[str, Any]:
        """
        Get basic information about the Moon using ephem for the given observer.
        Includes position, distance, phase, and next new/full moon dates.
        
        Parameters:
            observer: PyEphem observer object
            
        Returns:
            Dictionary containing basic Moon data
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
        prev_new = ephem.previous_new_moon(observer.date)
        prev_full = ephem.previous_full_moon(observer.date)
        
        # Calculate moon age (days since new moon)
        moon_age = observer.date - prev_new
        moon_age_days = float(moon_age) * 365.25  # Convert to days
        
        body_data["current_phase"] = round(self.ephem_body.phase, 2)
        body_data["moon_age"] = {
            "days": round(moon_age_days, 2),
            "percentage_of_cycle": round(moon_age_days / 29.53 * 100, 2)
        }
        
        body_data["phases"] = {
            "previous": [
                {"phase": "New Moon", "date": ephem.Date(prev_new).datetime().strftime("%Y-%m-%d %H:%M:%S UTC")},
                {"phase": "Full Moon", "date": ephem.Date(prev_full).datetime().strftime("%Y-%m-%d %H:%M:%S UTC")}
            ],
            "next": [
                {"phase": "New Moon", "date": ephem.Date(next_new).datetime().strftime("%Y-%m-%d %H:%M:%S UTC")},
                {"phase": "Full Moon", "date": ephem.Date(next_full).datetime().strftime("%Y-%m-%d %H:%M:%S UTC")}
            ]
        }
        
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
            location = utils.Topos(latitude_degrees=lat, longitude_degrees=lon)
            observer_at_t = earth.at(t) + location
            alt, az, _ = observer_at_t.observe(self.skyfield_body).apparent().altaz()
            body_data["position"]["precise_altitude"] = round(alt.degrees, 4)
            body_data["position"]["precise_azimuth"] = round(az.degrees, 4)

    def enhance_with_astropy(self, body_data: Dict[str, Any], current_time: datetime, 
                            lat: Optional[float], lon: Optional[float], has_location: bool) -> None:
        """
        Enhance the Moon data with advanced calculations using astropy.
        Adds precise constellation, libration, and illumination details.
        
        Parameters:
            body_data: Dictionary to be enhanced with additional data
            current_time: Current UTC time
            lat: Observer's latitude (if available)
            lon: Observer's longitude (if available)
            has_location: Boolean indicating if location is provided
        """
        try:
            # Convert to astropy time
            t = Time(current_time)
            
            # Get moon coordinates using astropy
            moon_coords = get_moon(t)
            
            # Convert to ICRS frame (International Celestial Reference System)
            moon_icrs = moon_coords.transform_to('icrs')
            
            # Get constellation with better precision
            constellation = get_constellation(moon_icrs)
            body_data["constellation_precise"] = constellation
            
            # Add illumination calculation
            try:
                # Get positions of sun and moon
                sun_coords = get_sun(t)
                
                # Calculate elongation (angular separation between Sun and Moon)
                elongation = sun_coords.separation(moon_coords).deg
                
                # Calculate phase angle and illuminated fraction
                phase_angle = abs(180 - elongation)
                illuminated_fraction = (1 + np.cos(np.radians(phase_angle))) / 2
                
                body_data["illumination_details"] = {
                    "elongation_degrees": round(elongation, 2),
                    "phase_angle_degrees": round(phase_angle, 2),
                    "illuminated_fraction": round(illuminated_fraction, 4),
                    "illuminated_percentage": round(illuminated_fraction * 100, 2)
                }
            except Exception as e:
                body_data["illumination_error"] = str(e)
            
            # Add libration calculation
            try:
                # Note: This is a simplified approximation of libration
                # For a full calculation, a dedicated lunar theory would be needed
                
                # Get geocentric ecliptic longitude and latitude
                ecliptic = moon_icrs.transform_to('geocentrictrueecliptic')
                lon_ecl = ecliptic.lon.deg
                lat_ecl = ecliptic.lat.deg
                
                # Simplified optical libration calculation
                # These are approximations based on the Moon's orbital inclination and eccentricity
                optical_libration_lon = 6.29 * np.sin(np.radians(lon_ecl))
                optical_libration_lat = 5.13 * np.sin(np.radians(lat_ecl))
                
                body_data["libration"] = {
                    "longitude_degrees": round(optical_libration_lon, 2),
                    "latitude_degrees": round(optical_libration_lat, 2),
                    "position_angle_degrees": round(np.arctan2(optical_libration_lat, optical_libration_lon) * 180 / np.pi, 2),
                    "note": "Simplified optical libration approximation"
                }
            except Exception as e:
                body_data["libration_error"] = str(e)
            
            # Add additional information if location provided
            if has_location:
                try:
                    # Create observer location
                    observer = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
                    
                    # Transform to horizontal coordinates (altitude/azimuth)
                    altaz_frame = AltAz(obstime=t, location=observer)
                    moon_altaz = moon_icrs.transform_to(altaz_frame)
                    
                    # Calculate atmospheric extinction
                    # Simple approximation based on altitude
                    if moon_altaz.alt.deg > 0:
                        extinction = 0.28 / np.sin(np.radians(moon_altaz.alt.deg))
                        if extinction > 5:
                            extinction = 5  # Cap at reasonable value
                    else:
                        extinction = 5  # Maximum extinction when below horizon
                    
                    body_data["viewing_conditions"] = {
                        "atmospheric_extinction": round(extinction, 2),
                        "extinction_effect": f"{round(extinction * 100, 1)}% dimming",
                        "best_viewing_time": "Around transit (highest altitude)"
                    }
                except Exception as e:
                    body_data["viewing_error"] = str(e)
        
        except Exception as e:
            body_data["astropy_error"] = str(e)

    def add_rise_set_times(self, body_data: Dict[str, Any], observer, has_location: bool) -> None:
        """
        Add next moonrise and moonset times to the data if location is provided.
        Handles circumpolar cases gracefully.
        
        Parameters:
            body_data: Dictionary to be enhanced with rise/set times
            observer: PyEphem observer object
            has_location: Boolean indicating if location is provided
        """
        if not has_location:
            return
            
        try:
            rise_set_info = {}
            
            # Standard atmospheric refraction
            observer.horizon = "-0:34"
            
            # Try to get next rise time
            try:
                next_rise = observer.next_rising(self.ephem_body)
                next_rise_time = next_rise.datetime()
                rise_set_info["next_moonrise"] = {
                    "time": next_rise_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "azimuth_degrees": round(math.degrees(float(self.ephem_body.az)), 2)
                }
                
                # Calculate Moon's illumination at rise time
                observer.date = next_rise
                self.ephem_body.compute(observer)
                rise_set_info["next_moonrise"]["illumination_percent"] = round(self.ephem_body.phase, 2)
                
                # Reset date to current
                observer.date = ephem.now()
                
            except ephem.CircumpolarError:
                rise_set_info["next_moonrise"] = "Moon is circumpolar - never rises"
            
            # Try to get next set time
            try:
                next_set = observer.next_setting(self.ephem_body)
                next_set_time = next_set.datetime()
                rise_set_info["next_moonset"] = {
                    "time": next_set_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "azimuth_degrees": round(math.degrees(float(self.ephem_body.az)), 2)
                }
                
                # Calculate Moon's illumination at set time
                observer.date = next_set
                self.ephem_body.compute(observer)
                rise_set_info["next_moonset"]["illumination_percent"] = round(self.ephem_body.phase, 2)
                
                # Reset date to current
                observer.date = ephem.now()
                
            except ephem.CircumpolarError:
                rise_set_info["next_moonset"] = "Moon is circumpolar - never sets"
            
            # Add transit time (when the moon is highest in the sky)
            try:
                next_transit = observer.next_transit(self.ephem_body)
                next_transit_time = next_transit.datetime()
                
                observer.date = next_transit
                self.ephem_body.compute(observer)
                
                rise_set_info["next_transit"] = {
                    "time": next_transit_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "altitude_degrees": round(math.degrees(float(self.ephem_body.alt)), 2),
                    "azimuth_degrees": round(math.degrees(float(self.ephem_body.az)), 2),
                    "illumination_percent": round(self.ephem_body.phase, 2)
                }
                
                # Reset date to current
                observer.date = ephem.now()
                
            except Exception:
                rise_set_info["next_transit"] = "Error calculating transit time"
                
            body_data["moonrise_and_set"] = rise_set_info
            
        except Exception as e:
            body_data["rise_set_error"] = str(e) 