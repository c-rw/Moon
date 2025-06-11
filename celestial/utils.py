"""
Utility module for astronomical calculations and shared resources.
Centralizes ephemeris loading and provides time scale conversion utilities.
"""
from skyfield import api
from skyfield.api import load, Topos
import numpy as np
from typing import Dict, Tuple, Any

# Load ephemeris data once - shared across all modules
# Using DE440 for increased precision over DE421
try:
    # Attempt to load the more precise DE440 ephemeris
    ts = load.timescale()
    eph = load('de440.bsp')
except Exception:
    # Fall back to DE421 if DE440 is not available
    ts = load.timescale()
    eph = load('de421.bsp')

# Common celestial objects
earth = eph['earth']
moon = eph['moon']
sun = eph['sun']
mars = eph['mars']
jupiter = eph['jupiter barycenter']
saturn = eph['saturn barycenter']

def get_time_scales(utc_time) -> Dict[str, Any]:
    """
    Convert UTC time to various astronomical time scales.
    
    Parameters:
        utc_time: datetime object in UTC
        
    Returns:
        Dictionary containing time objects in different scales:
        - t_utc: UTC time (Coordinated Universal Time)
        - t_tt: TT (Terrestrial Time)
        - t_tdb: TDB (Barycentric Dynamical Time)
    """
    t_utc = ts.from_datetime(utc_time)
    
    return {
        'utc': t_utc,
        'tt': ts.tt_jd(t_utc.tt),
        'tdb': ts.tdb_jd(t_utc.tdb)
    }

def get_topocentric_position(lat: float, lon: float, time_obj, body) -> Tuple[Any, Any]:
    """
    Calculate topocentric position of a celestial body.
    
    Parameters:
        lat: Observer's latitude in degrees
        lon: Observer's longitude in degrees
        time_obj: Skyfield time object
        body: Skyfield body object
        
    Returns:
        Tuple of (topocentric_position, observer_at_time)
    """
    location = Topos(latitude_degrees=lat, longitude_degrees=lon)
    observer_at_t = earth.at(time_obj) + location
    body_topocentric = observer_at_t.observe(body).apparent()
    
    return body_topocentric, observer_at_t

def radec_to_dict(ra, dec) -> Dict[str, Dict[str, float]]:
    """
    Convert right ascension and declination to a structured dictionary.
    
    Parameters:
        ra: Right ascension object from Skyfield
        dec: Declination object from Skyfield
        
    Returns:
        Dictionary with formatted right ascension and declination values
    """
    return {
        "right_ascension": {
            "hours": round(ra.hours, 4),
            "degrees": round(ra.hours * 15, 4),
            "hms": str(ra)
        },
        "declination": {
            "degrees": round(dec.degrees, 4),
            "dms": str(dec)
        }
    }

def altaz_to_dict(alt, az) -> Dict[str, Dict[str, float]]:
    """
    Convert altitude and azimuth to a structured dictionary.
    
    Parameters:
        alt: Altitude object from Skyfield
        az: Azimuth object from Skyfield
        
    Returns:
        Dictionary with formatted altitude and azimuth values
    """
    return {
        "altitude": {
            "degrees": round(alt.degrees, 4),
            "radians": round(float(alt.radians), 6)
        },
        "azimuth": {
            "degrees": round(az.degrees, 4),
            "radians": round(float(az.radians), 6)
        }
    }

def apply_aberration_nutation(position):
    """
    Apply aberration and nutation corrections to a position.
    
    Parameters:
        position: Skyfield position object
        
    Returns:
        Position with aberration and nutation corrections applied
    """
    # The .apparent() method applies both aberration and nutation corrections
    return position.apparent() 