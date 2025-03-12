from skyfield.api import load
from astropy.coordinates import get_constellation, SkyCoord
import astropy.units as u
import ephem

# Load planetary data
ts = load.timescale()
planets = load("de421.bsp")

# Observer location
latitude, longitude = 35.7478, -95.3697
observer = planets["earth"].topos(
    latitude_degrees=latitude, longitude_degrees=longitude
)

# Time of observation
t = ts.utc(2025, 3, 12, 0, 0, 22)

# Celestial objects
celestial_objects = {
    "Moon": planets["moon"],
    "Mars": planets["mars"],
    "Jupiter": planets["jupiter barycenter"],
    "Neptune": planets["neptune barycenter"],
}


def get_object_position(obj, observer, t):
    """Compute RA, DEC, and Constellation."""
    position = observer.at(t).observe(obj).apparent()
    ra, dec, _ = position.radec()

    # Convert RA/DEC to Constellation
    coord = SkyCoord(ra.hours * 15 * u.deg, dec.degrees * u.deg, frame="icrs")
    constellation = get_constellation(coord)

    return {
        "RA": round(ra.hours * 15, 2),
        "DEC": round(dec.degrees, 2),
        "Constellation": constellation,
    }


# Compute celestial positions
results = {
    obj: get_object_position(celestial_objects[obj], observer, t)
    for obj in celestial_objects
}

# ✅ **Use ephem for local altitude/azimuth**
obs = ephem.Observer()
obs.lat, obs.lon = str(latitude), str(longitude)
obs.date = "2025/03/12 00:00:22"

moon = ephem.Moon(obs)
results["Moon"].update(
    {
        "Altitude": round(float(moon.alt) * 57.2958, 2),  # Convert radians to degrees
        "Azimuth": round(float(moon.az) * 57.2958, 2),  # Convert radians to degrees
    }
)

# Print results
import json

print(json.dumps(results, indent=4))
