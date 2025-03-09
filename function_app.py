import azure.functions as func
import logging
import ephem
from datetime import datetime, timezone
import json
import math

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="moon")
def moon(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processing moon information request.")

    # Create ephem objects
    moon = ephem.Moon()
    observer = ephem.Observer()

    # Set current time
    current_time = datetime.now(timezone.utc)
    observer.date = current_time

    # Get optional location parameters
    has_location = False
    try:
        if req.method == "POST" and req.get_body():
            try:
                req_body = req.get_json()

                # Check if both latitude and longitude are provided
                if "latitude" in req_body and "longitude" in req_body:
                    # Validate latitude and longitude
                    try:
                        lat = float(req_body.get("latitude"))
                        lon = float(req_body.get("longitude"))

                        # Check if values are in valid ranges
                        if -90 <= lat <= 90 and -180 <= lon <= 180:
                            observer.lat = str(lat)
                            observer.lon = str(lon)
                            has_location = True
                        else:
                            return func.HttpResponse(
                                json.dumps(
                                    {
                                        "error": "Invalid latitude or longitude values. Latitude must be between -90 and 90, longitude between -180 and 180."
                                    }
                                ),
                                mimetype="application/json",
                                status_code=400,
                            )
                    except (ValueError, TypeError):
                        return func.HttpResponse(
                            json.dumps(
                                {
                                    "error": "Latitude and longitude must be valid numbers."
                                }
                            ),
                            mimetype="application/json",
                            status_code=400,
                        )
            except ValueError:
                return func.HttpResponse(
                    json.dumps({"error": "Invalid JSON in request body."}),
                    mimetype="application/json",
                    status_code=400,
                )
    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")

    # Calculate moon information with error handling
    try:
        moon.compute(observer)
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": f"Failed to compute moon information: {str(e)}"}),
            mimetype="application/json",
            status_code=500,
        )

    # Calculate next moon phases
    next_new = ephem.next_new_moon(observer.date)
    next_full = ephem.next_full_moon(observer.date)

    # Convert altitude and azimuth from radians to degrees for better readability
    altitude_deg = math.degrees(float(moon.alt))
    azimuth_deg = math.degrees(float(moon.az))

    # Prepare response data
    moon_data = {
        "current_phase": round(
            moon.phase, 2
        ),  # Phase as percentage illuminated, rounded to 2 decimal places
        "next_phases": [
            {
                "phase": "New Moon",
                "date": ephem.Date(next_new)
                .datetime()
                .strftime("%Y-%m-%d %H:%M:%S UTC"),
            },
            {
                "phase": "Full Moon",
                "date": ephem.Date(next_full)
                .datetime()
                .strftime("%Y-%m-%d %H:%M:%S UTC"),
            },
        ],
        "altitude": {"degrees": round(altitude_deg, 2), "radians": str(moon.alt)},
        "azimuth": {"degrees": round(azimuth_deg, 2), "radians": str(moon.az)},
        "distance": f"{int(moon.earth_distance * 149597870.691)} km",  # Converting AU to kilometers
        "constellation": ephem.constellation(moon)[1],
        "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
    }

    # Add observer info and rise/set info if location was provided
    if has_location:
        # Calculate moonrise and moonset
        rise_set_info = {}
        observer.horizon = "-0:34"  # Standard atmospheric refraction

        # Get next rise and set times
        try:
            next_rise = observer.next_rising(moon).datetime()
            rise_set_info["next_moonrise"] = next_rise.strftime("%Y-%m-%d %H:%M:%S UTC")
        except ephem.CircumpolarError:
            rise_set_info["next_moonrise"] = "Moon is circumpolar - never rises"

        try:
            next_set = observer.next_setting(moon).datetime()
            rise_set_info["next_moonset"] = next_set.strftime("%Y-%m-%d %H:%M:%S UTC")
        except ephem.CircumpolarError:
            rise_set_info["next_moonset"] = "Moon is circumpolar - never sets"

        moon_data["moonrise_and_set"] = rise_set_info
        moon_data["observer"] = {
            "latitude": float(observer.lat) if hasattr(observer, "lat") else None,
            "longitude": float(observer.lon) if hasattr(observer, "lon") else None,
        }

    return func.HttpResponse(
        json.dumps(moon_data), mimetype="application/json", status_code=200
    )
