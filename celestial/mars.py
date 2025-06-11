from .base import CelestialBody
import ephem
import math
from datetime import datetime
from typing import Dict, Any, Optional
import numpy as np

from astropy.coordinates import get_constellation, EarthLocation, AltAz, get_body
from astropy.time import Time
import astropy.units as u

from . import utils

# Load skyfield data (shared, but for now, load here)
ts = utils.load.timescale()
eph = utils.load('de421.bsp')
earth = eph['earth']

class Mars(CelestialBody):
    """
    CelestialBody subclass for Mars. Implements all required astronomical calculations and enhancements.
    Includes topocentric corrections, time scale handling, and nutation/aberration corrections.
    """
    def __init__(self):
        super().__init__('mars')
        self.ephem_body = ephem.Mars()  # PyEphem object for Mars
        self.skyfield_body = utils.mars  # Skyfield object for Mars

    def get_basic_info(self, observer) -> Dict[str, Any]:
        """
        Get basic information about Mars using ephem for the given observer.
        Includes position, distance, and constellation.
        
        Parameters:
            observer: PyEphem observer object
            
        Returns:
            Dictionary containing basic Mars data
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
            "constellation": ephem.constellation(self.ephem_body)[1],
            "magnitude": round(float(self.ephem_body.mag), 2),
            "angular_diameter": {
                "arcseconds": round(float(self.ephem_body.size) / 60, 2)  # Convert to arcseconds
            }
        }
        
        # Add Mars-specific information - opposition and conjunction
        try:
            # Calculate next opposition (Mars opposite the Sun)
            # This is a simplified approach - using the Sun-Earth-Mars angle
            sun = ephem.Sun()
            sun.compute(observer)
            
            # Sun's longitude from Earth
            sun_lon = float(sun.hlong)
            
            # Mars' longitude from Earth
            mars_lon = float(self.ephem_body.hlong)
            
            # Angular separation
            angular_sep = abs((mars_lon - sun_lon) % (2 * math.pi))
            
            # Mars is at opposition when it's opposite the Sun in the sky (separation ~180°)
            # Mars is at conjunction when it's in the same direction as the Sun (separation ~0°)
            body_data["sun_separation"] = {
                "degrees": round(math.degrees(angular_sep), 2),
                "opposition_proximity": round(abs(180 - math.degrees(angular_sep)), 2)
            }
            
            # Add note about opposition or conjunction
            if abs(math.degrees(angular_sep) - 180) < 15:
                body_data["special_position"] = "Near opposition (good for viewing)"
            elif abs(math.degrees(angular_sep)) < 15:
                body_data["special_position"] = "Near conjunction (difficult to observe)"
                
        except Exception as e:
            body_data["opposition_error"] = str(e)
        
        return body_data

    def enhance_with_skyfield(self, body_data, current_time, lat, lon, has_location):
        """
        Enhance the Mars data with more precise calculations using skyfield.
        Adds celestial coordinates and precise distance. If location is provided, adds precise altitude/azimuth.
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
        Enhance the Mars data with advanced calculations using astropy.
        Adds precise constellation and viewing conditions.
        
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
            
            # Get Mars coordinates using astropy
            mars_coords = get_body('mars', t)
            
            # Convert to ICRS frame (International Celestial Reference System)
            mars_icrs = mars_coords.transform_to('icrs')
            
            # Get constellation with better precision
            constellation = get_constellation(mars_icrs)
            body_data["constellation_precise"] = constellation
            
            # Get physical details for Mars
            try:
                # Add information about Mars' season (based on areocentric longitude Ls)
                # This is a simplified calculation
                from astropy.coordinates import solar_system_ephemeris
                solar_system_ephemeris.set('builtin')
                
                # Calculate Mars year and season
                # Mars year is counted from the first Mars year beginning after April 11, 1955
                # Year length is approximately 687 Earth days
                
                # Days since epoch
                days_since_epoch = (current_time.date() - datetime(1955, 4, 11).date()).days
                
                # Mars years since epoch
                mars_years = days_since_epoch / 687
                
                # Mars year number (MY)
                my_number = int(mars_years) + 1
                
                # Calculate approximate Ls (areocentric longitude of the Sun)
                # This is a very simplified calculation
                ls_deg = ((mars_years % 1) * 360) % 360
                
                # Determine Martian season based on Ls
                if 0 <= ls_deg < 90:
                    season = "Northern Spring / Southern Autumn"
                elif 90 <= ls_deg < 180:
                    season = "Northern Summer / Southern Winter"
                elif 180 <= ls_deg < 270:
                    season = "Northern Autumn / Southern Spring"
                else:
                    season = "Northern Winter / Southern Summer"
                
                body_data["mars_seasons"] = {
                    "mars_year": my_number,
                    "solar_longitude_deg": round(ls_deg, 2),
                    "season": season
                }
                
            except Exception as e:
                body_data["mars_seasons_error"] = str(e)
            
            # Add additional information if location provided
            if has_location:
                try:
                    # Create observer location
                    observer = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
                    
                    # Transform to horizontal coordinates (altitude/azimuth)
                    altaz_frame = AltAz(obstime=t, location=observer)
                    mars_altaz = mars_icrs.transform_to(altaz_frame)
                    
                    # Calculate atmospheric extinction
                    # Simple approximation based on altitude
                    if mars_altaz.alt.deg > 0:
                        extinction = 0.28 / np.sin(np.radians(mars_altaz.alt.deg))
                        if extinction > 5:
                            extinction = 5  # Cap at reasonable value
                    else:
                        extinction = 5  # Maximum extinction when below horizon
                    
                    # Calculate best viewing conditions based on altitude and Mars' position
                    best_time = "During astronomical night when at highest altitude"
                    if body_data.get("special_position") == "Near opposition (good for viewing)":
                        best_time += " (currently near opposition, excellent viewing)"
                    
                    body_data["viewing_conditions"] = {
                        "atmospheric_extinction": round(extinction, 2),
                        "extinction_effect": f"{round(extinction * 100, 1)}% dimming",
                        "best_viewing_time": best_time,
                        "apparent_magnitude_with_extinction": round(body_data["magnitude"] + extinction, 2)
                    }
                except Exception as e:
                    body_data["viewing_error"] = str(e)
        
        except Exception as e:
            body_data["astropy_error"] = str(e)

    def add_rise_set_times(self, body_data: Dict[str, Any], observer, has_location: bool) -> None:
        """
        Add next marsrise and marsset times to the data if location is provided.
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
                rise_set_info["next_marsrise"] = {
                    "time": next_rise_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "azimuth_degrees": round(math.degrees(float(self.ephem_body.az)), 2)
                }
                
                # Calculate Mars' magnitude at rise time
                observer.date = next_rise
                self.ephem_body.compute(observer)
                rise_set_info["next_marsrise"]["magnitude"] = round(float(self.ephem_body.mag), 2)
                
                # Reset date to current
                observer.date = ephem.now()
                
            except ephem.CircumpolarError:
                rise_set_info["next_marsrise"] = "Mars is circumpolar - never rises"
            
            # Try to get next set time
            try:
                next_set = observer.next_setting(self.ephem_body)
                next_set_time = next_set.datetime()
                rise_set_info["next_marsset"] = {
                    "time": next_set_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "azimuth_degrees": round(math.degrees(float(self.ephem_body.az)), 2)
                }
                
                # Calculate Mars' magnitude at set time
                observer.date = next_set
                self.ephem_body.compute(observer)
                rise_set_info["next_marsset"]["magnitude"] = round(float(self.ephem_body.mag), 2)
                
                # Reset date to current
                observer.date = ephem.now()
                
            except ephem.CircumpolarError:
                rise_set_info["next_marsset"] = "Mars is circumpolar - never sets"
            
            # Add transit time (when Mars is highest in the sky)
            try:
                next_transit = observer.next_transit(self.ephem_body)
                next_transit_time = next_transit.datetime()
                
                observer.date = next_transit
                self.ephem_body.compute(observer)
                
                rise_set_info["next_transit"] = {
                    "time": next_transit_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "altitude_degrees": round(math.degrees(float(self.ephem_body.alt)), 2),
                    "azimuth_degrees": round(math.degrees(float(self.ephem_body.az)), 2),
                    "magnitude": round(float(self.ephem_body.mag), 2)
                }
                
                # Reset date to current
                observer.date = ephem.now()
                
            except Exception:
                rise_set_info["next_transit"] = "Error calculating transit time"
                
            body_data["marsrise_and_set"] = rise_set_info
            
        except Exception as e:
            body_data["rise_set_error"] = str(e) 