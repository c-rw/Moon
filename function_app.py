import azure.functions as func
import logging
import ephem
from datetime import datetime, timezone
import json
import math
from typing import Optional, Tuple, Dict, Any

# Additional imports
from celestial import utils
from celestial.moon import Moon
from celestial.mars import Mars

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

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
        # Get basic info and enhance with additional calculations
        body_data = body.get_basic_info(observer)
        
        # Apply enhancements with advanced libraries
        body.enhance_with_skyfield(body_data, current_time, lat, lon, has_location)
        body.enhance_with_astropy(body_data, current_time, lat, lon, has_location)
        
        # Add timestamp in multiple time scales
        time_scales = utils.get_time_scales(current_time)
        body_data["timestamp"] = current_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        body_data["time_scales"] = {
            "utc": current_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "tt": time_scales['tt'].utc_strftime("%Y-%m-%d %H:%M:%S TT"),
            "tdb": time_scales['tdb'].utc_strftime("%Y-%m-%d %H:%M:%S TDB")
        }
        
        # Add observer details if location was provided
        if has_location:
            body_data["observer"] = {
                "latitude": lat, 
                "longitude": lon,
                "geodetic_height": 0,  # Assumed to be at sea level
                "reference_frame": "WGS84"
            }
            body.add_rise_set_times(body_data, observer, has_location)
        
        # Add metadata about calculations
        body_data["calculation_metadata"] = {
            "libraries_used": ["ephem", "skyfield", "astropy"],
            "ephemeris_used": utils.eph.names[0],
            "nutation_correction_applied": True,
            "aberration_correction_applied": True,
            "topocentric_correction_applied": has_location,
            "api_version": "1.1.0"
        }
        
        return func.HttpResponse(json.dumps(body_data), mimetype="application/json", status_code=200)
    except Exception as e:
        logging.error(f"Error calculating {body_name} information: {str(e)}")
        return error_response(f"Failed to compute {body_name} information: {str(e)}", 500)

def error_response(message: str, status_code: int = 400) -> func.HttpResponse:
    """
    Standardized error response helper for returning JSON error messages.
    """
    return func.HttpResponse(json.dumps({"error": message}), mimetype="application/json", status_code=status_code)

# For future expansion, additional celestial body routes can be added here
# @app.route(route="jupiter")
# def jupiter(req: func.HttpRequest) -> func.HttpResponse:
#     return get_celestial_body_info(req, 'jupiter')
# 
# @app.route(route="saturn")
# def saturn(req: func.HttpRequest) -> func.HttpResponse:
#     return get_celestial_body_info(req, 'saturn')