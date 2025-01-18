import azure.functions as func
import logging
import ephem
from datetime import datetime, timedelta
import json

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="moon")
def moon(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processing moon information request.')
    
    # Create ephem objects
    moon = ephem.Moon()
    observer = ephem.Observer()
    
    # Get optional location parameters
    try:
        req_body = req.get_json()
        has_location = True
    except ValueError:
        req_body = {}
        has_location = False
    
    # Set observer location (defaults to Greenwich if not provided)
    lat = req_body.get('latitude', '51.4769')  # Greenwich latitude
    lon = req_body.get('longitude', '0.0005')  # Greenwich longitude
    
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.date = datetime.utcnow()
    
    # Calculate moon information
    moon.compute(observer)
    
    # Calculate next moon phases
    next_new = ephem.next_new_moon(observer.date)
    next_full = ephem.next_full_moon(observer.date)
    
    # Calculate moonrise and moonset if location provided
    rise_set_info = {}
    if has_location:
        # Get next moonrise and moonset
        observer.horizon = '-0:34'  # Standard atmospheric refraction
        
        # Get next rise and set times
        try:
            next_rise = observer.next_rising(moon).datetime()
            rise_set_info['next_moonrise'] = next_rise.strftime('%Y-%m-%d %H:%M:%S UTC')
        except ephem.CircumpolarError:
            rise_set_info['next_moonrise'] = "Moon is circumpolar - never rises"
            
        try:
            next_set = observer.next_setting(moon).datetime()
            rise_set_info['next_moonset'] = next_set.strftime('%Y-%m-%d %H:%M:%S UTC')
        except ephem.CircumpolarError:
            rise_set_info['next_moonset'] = "Moon is circumpolar - never sets"
    
    # Prepare response data
    moon_data = {
        'current_phase': moon.phase,  # Phase as percentage illuminated
        'next_phases': [
            {
                'phase': 'New Moon',
                'date': ephem.Date(next_new).datetime().strftime('%Y-%m-%d %H:%M:%S UTC')
            },
            {
                'phase': 'Full Moon',
                'date': ephem.Date(next_full).datetime().strftime('%Y-%m-%d %H:%M:%S UTC')
            }
        ],
        'altitude': str(moon.alt),  # Height above horizon in radians
        'azimuth': str(moon.az),    # Position along horizon in radians
        'distance': f"{moon.earth_distance * 149597870.691:.0f} km",  # Converting AU to kilometers
        'constellation': ephem.constellation(moon)[1],
        'observer': {
            'latitude': lat,
            'longitude': lon,
            'timestamp': observer.date.datetime().strftime('%Y-%m-%d %H:%M:%S UTC')
        }
    }
    
    # Add rise/set info if location was provided
    if has_location:
        moon_data['moonrise_and_set'] = rise_set_info
    
    return func.HttpResponse(
        json.dumps(moon_data, indent=2),
        mimetype="application/json",
        status_code=200
    )