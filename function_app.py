import azure.functions as func
import logging
import ephem
from datetime import datetime
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
    except ValueError:
        req_body = {}
    
    # Set observer location (defaults to Greenwich if not provided)
    lat = req_body.get('latitude', '51.4769')  # Greenwich latitude
    lon = req_body.get('longitude', '0.0005')  # Greenwich longitude
    
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.date = datetime.utcnow()
    
    # Calculate moon information
    moon.compute(observer)
    
    # Calculate next four moon phases
    next_phases = []
    current_date = ephem.Date(datetime.utcnow())
    
    for phase in [ephem.next_new_moon, ephem.next_first_quarter,
                 ephem.next_full_moon, ephem.next_last_quarter]:
        next_date = phase(current_date)
        phase_name = phase.__name__.replace('next_', '').replace('_', ' ').title()
        next_phases.append({
            'phase': phase_name,
            'date': ephem.Date(next_date).datetime().strftime('%Y-%m-%d %H:%M:%S UTC')
        })
    
    # Prepare response data
    moon_data = {
        'current_phase': moon.phase,  # Phase as percentage illuminated
        'next_phases': next_phases,
        'altitude': str(moon.alt),  # Height above horizon in radians
        'azimuth': str(moon.az),    # Position along horizon in radians
        'distance': f"{moon.earth_distance:.1f} AU",
        'constellation': ephem.constellation(moon)[1],
        'observer': {
            'latitude': lat,
            'longitude': lon,
            'timestamp': observer.date.datetime().strftime('%Y-%m-%d %H:%M:%S UTC')
        }
    }
    
    return func.HttpResponse(
        json.dumps(moon_data, indent=2),
        mimetype="application/json",
        status_code=200
    )