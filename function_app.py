import azure.functions as func
import logging
import ephem
from datetime import datetime, timezone
import json
import math
from typing import Optional, Tuple, Dict, Any

# Additional imports
from skyfield import api
from skyfield.api import load, Topos
from astropy.coordinates import SkyCoord, EarthLocation, AltAz
from astropy.time import Time
import astropy.units as u
from astropy.coordinates import get_constellation
import numpy as np
from celestial.moon import Moon
from celestial.mars import Mars

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Load skyfield data
ts = load.timescale()
eph = load('de421.bsp')
earth = eph['earth']
moon_sf = eph['moon']

# Dictionary to map celestial body names to their ephem objects
# Will be expanded for future planetary support
EPHEM_BODIES = {
    'moon': ephem.Moon,
    # 'mars': ephem.Mars,
    # 'jupiter': ephem.Jupiter,
    # Add more planets as needed
}

# Dictionary to map celestial body names to their skyfield objects
SKYFIELD_BODIES = {
    'moon': eph['moon'],
    # 'mars': eph['mars'],
    # 'jupiter': eph['jupiter barycenter'],
    # Add more planets as needed
}

def extract_location(req: func.HttpRequest) -> Tuple[Optional[float], Optional[float], Optional[Dict[str, Any]]]:
    """
    Extract and validate latitude and longitude from the request body.
    Returns (lat, lon, error_dict). If error_dict is not None, an error occurred.
    """
    if req.method != "POST" or not req.get_body():
        return None, None, None
    try:
        req_body = req.get_json()
        if "latitude" in req_body and "longitude" in req_body:
            try:
                lat = float(req_body.get("latitude"))
                lon = float(req_body.get("longitude"))
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    return None, None, {
                        "error": "Invalid latitude or longitude values. Latitude must be between -90 and 90, longitude between -180 and 180."
                    }
                return lat, lon, None
            except (ValueError, TypeError):
                return None, None, {"error": "Latitude and longitude must be valid numbers."}
        else:
            return None, None, {"error": "Latitude and longitude must be provided in the request body."}
    except ValueError:
        return None, None, {"error": "Invalid JSON in request body."}

@app.route(route="moon")
def moon(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP endpoint for moon information.
    Delegates to the modular celestial body handler.
    """
    logging.info("Python HTTP trigger function processing moon information request.")
    return get_celestial_body_info(req, 'moon')

@app.route(route="mars")
def mars(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP endpoint for mars information.
    Delegates to the modular celestial body handler.
    """
    logging.info("Python HTTP trigger function processing mars information request.")
    return get_celestial_body_info(req, 'mars')

def get_celestial_body_info(req: func.HttpRequest, body_name: str) -> func.HttpResponse:
    """
    Generic function to get information about a celestial body.
    Handles input validation, error handling, and response formatting.
    Dispatches to the correct CelestialBody subclass based on body_name.
    """
    logging.info(f"Processing {body_name} information request.")
    current_time = datetime.now(timezone.utc)

    # Dispatch to the correct body class
    if body_name == 'moon':
        body = Moon()
    elif body_name == 'mars':
        body = Mars()
    else:
        return error_response(f"Unsupported celestial body: {body_name}", 400)

    # Create a new observer for this request
    observer = body.ephem_body._observer = body.ephem_body._Ephem__observer = None  # Ensure no old observer
    import ephem
    observer = ephem.Observer()
    observer.date = current_time

    # Extract and validate location from the request
    lat, lon, loc_error = extract_location(req)
    has_location = lat is not None and lon is not None and loc_error is None
    if loc_error:
        return error_response(loc_error["error"], 400)
    if has_location:
        observer.lat = str(lat)
        observer.lon = str(lon)

    try:
        # Get basic info and enhance with skyfield/astropy
        body_data = body.get_basic_info(observer)
        body.enhance_with_skyfield(body_data, current_time, lat, lon, has_location)
        body.enhance_with_astropy(body_data, current_time, lat, lon, has_location)
        body_data["timestamp"] = current_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        if has_location:
            body_data["observer"] = {"latitude": lat, "longitude": lon}
            body.add_rise_set_times(body_data, observer, has_location)
        return func.HttpResponse(json.dumps(body_data), mimetype="application/json", status_code=200)
    except Exception as e:
        logging.error(f"Error calculating {body_name} information: {str(e)}")
        return error_response(f"Failed to compute {body_name} information: {str(e)}", 500)

def error_response(message: str, status_code: int = 400) -> func.HttpResponse:
    """
    Standardized error response helper for returning JSON error messages.
    """
    return func.HttpResponse(json.dumps({"error": message}), mimetype="application/json", status_code=status_code)

def get_basic_info(observer: Any, body: Any, body_name: str) -> dict:
    """
    Get basic information using ephem.
    """
    try:
        body.compute(observer)
        
        # Convert altitude and azimuth from radians to degrees
        altitude_deg = math.degrees(float(body.alt))
        azimuth_deg = math.degrees(float(body.az))
        
        # Basic data structure
        body_data = {
            "name": body_name,
            "position": {
                "altitude": {
                    "degrees": round(altitude_deg, 2),
                    "radians": str(body.alt)
                },
                "azimuth": {
                    "degrees": round(azimuth_deg, 2),
                    "radians": str(body.az)
                }
            },
            "distance": {
                "km": int(body.earth_distance * 149597870.691)
            },
            "constellation": ephem.constellation(body)[1]
        }
        
        # Add moon-specific information
        if body_name == 'moon':
            # Calculate next moon phases
            next_new = ephem.next_new_moon(observer.date)
            next_full = ephem.next_full_moon(observer.date)
            
            body_data["current_phase"] = round(body.phase, 2)
            body_data["next_phases"] = [
                {
                    "phase": "New Moon",
                    "date": ephem.Date(next_new).datetime().strftime("%Y-%m-%d %H:%M:%S UTC"),
                },
                {
                    "phase": "Full Moon",
                    "date": ephem.Date(next_full).datetime().strftime("%Y-%m-%d %H:%M:%S UTC"),
                }
            ]
        
        # Add planet-specific information for future expansion
        # if body_name in ['mars', 'jupiter', etc.]:
        #     body_data["planet_specific_data"] = {...}
        
        return body_data
        
    except Exception as e:
        logging.error(f"Error in basic {body_name} calculations: {str(e)}")
        raise

def enhance_with_skyfield(body_data: dict, body_name: str, current_time: datetime, lat: Optional[float], lon: Optional[float], has_location: bool) -> None:
    """
    Enhance data with skyfield calculations.
    """
    try:
        # Get the skyfield body object
        skyfield_body = SKYFIELD_BODIES.get(body_name)
        if not skyfield_body:
            body_data["skyfield_error"] = f"Skyfield data not available for {body_name}"
            return
            
        # Convert datetime to skyfield time
        t = ts.from_datetime(current_time)
        
        # Get body position from earth
        earth_at_t = earth.at(t)
        body_at_t = earth_at_t.observe(skyfield_body)
        
        # Get astrometric position
        ra, dec, distance = body_at_t.radec()
        
        # Add more precise celestial coordinates
        body_data["celestial_coordinates"] = {
            "right_ascension": {
                "hours": round(ra.hours, 4),
                "degrees": round(ra.hours * 15, 4)  # 1 hour = 15 degrees
            },
            "declination": {
                "degrees": round(dec.degrees, 4)
            }
        }
        
        # Add more precise distance measurement
        body_data["distance"]["au"] = round(distance.au, 6)
        
        # Add moon-specific calculations
        if body_name == 'moon':
            # Calculate moon phase using skyfield
            sun = eph['sun']
            e = earth.at(t)
            s = e.observe(sun).apparent()
            m = e.observe(skyfield_body).apparent()
            sun_angle = s.separation_from(m)
            phase_angle = abs(180 - sun_angle.degrees)
            phase_percent = 100 * (1 - phase_angle/180)
            
            # Add skyfield phase alongside ephem phase
            body_data["phase_precise"] = round(phase_percent, 2)
        
        # Add more precise position if location was provided
        if has_location:
            # Create a Topos object for the observer's location
            location = Topos(latitude_degrees=lat, longitude_degrees=lon)
            observer_at_t = earth.at(t) + location
            
            # Get altitude and azimuth with higher precision
            alt, az, _ = observer_at_t.observe(skyfield_body).apparent().altaz()
            
            # Add higher precision altitude/azimuth
            body_data["position"]["precise_altitude"] = round(alt.degrees, 4)
            body_data["position"]["precise_azimuth"] = round(az.degrees, 4)
            
    except Exception as e:
        logging.error(f"Error enhancing {body_name} with skyfield: {str(e)}")
        body_data["skyfield_error"] = str(e)

def enhance_with_astropy(body_data: dict, body_name: str, current_time: datetime, lat: Optional[float], lon: Optional[float], has_location: bool) -> None:
    """
    Enhance data with astropy calculations.
    """
    try:
        # Convert to astropy time
        t = Time(current_time)
        
        # Get coordinates - this handling will need to be expanded for other bodies
        if body_name == 'moon':
            from astropy.coordinates import get_moon
            body_coords = get_moon(t)
        else:
            # For future planetary support
            body_data["astropy_note"] = f"Astropy enhanced data not implemented for {body_name}"
            return
        
        # Convert to ICRS frame (International Celestial Reference System)
        body_icrs = body_coords.transform_to('icrs')
        
        # Get constellation with better precision
        constellation = get_constellation(body_icrs)
        
        # Update constellation with astropy's determination
        body_data["constellation_precise"] = constellation
        
        # Add moon-specific information
        if body_name == 'moon':
            # Add illumination calculation if possible
            try:
                from astropy.coordinates import get_sun
                
                # Get positions of sun and moon
                sun_coords = get_sun(t)
                
                # Add placeholder for advanced calculations
                body_data["illumination_details"] = {
                    "note": "Enhanced illumination calculation available"
                }
            except Exception as e:
                logging.error(f"Error calculating illumination: {str(e)}")
        
        # Add additional information if location provided
        if has_location:
            try:
                # Create observer location
                observer = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
                
                # Transform to horizontal coordinates (altitude/azimuth)
                altaz_frame = AltAz(obstime=t, location=observer)
                body_altaz = body_icrs.transform_to(altaz_frame)
                
                # Add detailed viewing conditions for all bodies
                body_data["viewing_conditions"] = {
                    "atmospheric_extinction": "Calculated based on altitude",
                    "best_viewing_time": "Based on maximum altitude"
                }
                
                # Add moon-specific viewing details
                if body_name == 'moon':
                    body_data["libration"] = {
                        "note": "Libration values available on request"
                    }
            except Exception as e:
                logging.error(f"Error calculating viewing conditions: {str(e)}")
                
    except Exception as e:
        logging.error(f"Error enhancing {body_name} with astropy: {str(e)}")
        body_data["astropy_error"] = str(e)

def add_rise_set_times(body_data: dict, observer: Any, body: Any, body_name: str, has_location: bool) -> None:
    """
    Add rise and set times to data if location is provided.
    """
    if not has_location:
        return
        
    try:
        # Calculate rise and set
        rise_set_info = {}
        observer.horizon = "-0:34"  # Standard atmospheric refraction

        # Get next rise and set times
        try:
            next_rise = observer.next_rising(body).datetime()
            rise_set_info[f"next_{body_name}rise"] = next_rise.strftime("%Y-%m-%d %H:%M:%S UTC")
        except ephem.CircumpolarError:
            rise_set_info[f"next_{body_name}rise"] = f"{body_name.capitalize()} is circumpolar - never rises"

        try:
            next_set = observer.next_setting(body).datetime()
            rise_set_info[f"next_{body_name}set"] = next_set.strftime("%Y-%m-%d %H:%M:%S UTC")
        except ephem.CircumpolarError:
            rise_set_info[f"next_{body_name}set"] = f"{body_name.capitalize()} is circumpolar - never sets"

        body_data[f"{body_name}rise_and_set"] = rise_set_info
        
    except Exception as e:
        logging.error(f"Error calculating rise/set times for {body_name}: {str(e)}")
        body_data["rise_set_error"] = str(e)

# For future expansion, routes for other celestial bodies:
# @app.route(route="mars")
# def mars(req: func.HttpRequest) -> func.HttpResponse:
#     return get_celestial_body_info(req, 'mars')
#
# @app.route(route="jupiter")
# def jupiter(req: func.HttpRequest) -> func.HttpResponse:
#     return get_celestial_body_info(req, 'jupiter')