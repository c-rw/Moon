# Celestial Bodies Information API

An Azure Function API that provides detailed information about celestial bodies, currently supporting the Moon and Mars. The codebase is modular and easily extensible—new bodies can be added with minimal effort. The API uses multiple astronomical calculation libraries for enhanced precision and detailed information.

## Features

- **Current position** (altitude, azimuth, right ascension, declination)
- **Distance from Earth** in kilometers and astronomical units
- **Current constellation** (with multiple determination methods)
- **Rise and set times** (when location is provided)
- **Advanced viewing conditions** (atmospheric information)
- **Topocentric corrections** for precise local observations
- **Proper handling of time scales** (UTC, TT, TDB)
- **Nutation and aberration corrections** for high-precision positions
- **Ephemeris upgrades** (uses DE440 if available, falls back to DE421)
- **Moon-specific:**
  - Current phase (percentage illuminated)
  - Next new moon and full moon dates
  - Libration (on request)

## Precision & Corrections

- **Topocentric Corrections:** All positions are corrected for the observer's actual location on Earth's surface, not just geocentric (Earth center) positions.
- **Time Scales:** The API provides and uses UTC, TT (Terrestrial Time), and TDB (Barycentric Dynamical Time) as appropriate for each calculation. These are included in the response.
- **Nutation & Aberration:** All positions are corrected for nutation (Earth's axis wobble) and aberration (light travel effects) using the latest available ephemeris.
- **Ephemeris:** The API uses the JPL DE440 ephemeris for highest precision if available, falling back to DE421 if not. The ephemeris used is reported in the response.
- **Uncertainty Estimates:** The API includes approximate uncertainty and reference frame information in the response.

## Libraries Used

- **`ephem`**: For basic planetary calculations, moon phase, and rise/set times
- **`skyfield`**: For precise astronomical positioning and distance calculations, time scale handling, and corrections
- **`astropy`**: For advanced constellation determination and coordinate handling

## Prerequisites

- Python 3.10 or higher
- Azure Functions Core Tools
- Python Azure Functions dependencies

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/celestial-bodies-api.git
cd celestial-bodies-api
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. **Initialize ephemeris and star catalog data:**

```bash
python initialize.py
```

## Usage

### Starting the API Locally

Run the API locally using Azure Functions Core Tools:

```bash
func start
```

The API will be available at `http://localhost:7071/api/<body>` (e.g., `/moon`, `/mars`).

### API Endpoints

#### Basic Moon Information (GET)

```bash
curl http://localhost:7071/api/moon
```

#### Location-Specific Moon Information (POST)

```bash
curl -X POST \
  http://localhost:7071/api/moon \
  -H "Content-Type: application/json" \
  -d '{"latitude": 35.7478, "longitude": -95.3697}'
```

#### Basic Mars Information (GET)

```bash
curl http://localhost:7071/api/mars
```

#### Location-Specific Mars Information (POST)

```bash
curl -X POST \
  http://localhost:7071/api/mars \
  -H "Content-Type: application/json" \
  -d '{"latitude": 35.7478, "longitude": -95.3697}'
```

Note: Latitude must be between -90 and 90, longitude between -180 and 180.

### Example Moon Response

```json
{
  "name": "moon",
  "current_phase": 82.61,
  "moon_age": {"days": 14.2, "percentage_of_cycle": 48.1},
  "phases": {
    "previous": [
      { "phase": "New Moon", "date": "2025-01-15 12:35:54 UTC" },
      { "phase": "Full Moon", "date": "2025-01-01 13:53:19 UTC" }
    ],
    "next": [
      { "phase": "New Moon", "date": "2025-01-29 12:35:54 UTC" },
      { "phase": "Full Moon", "date": "2025-02-12 13:53:19 UTC" }
    ]
  },
  "position": {
    "altitude": { "degrees": -6.97, "radians": "-0:06:57.6" },
    "azimuth": { "degrees": 78.30, "radians": "78:18:12.0" }
  },
  "celestial_coordinates": {
    "right_ascension": { "hours": 10.8456, "degrees": 162.6840 },
    "declination": { "degrees": 8.5723 }
  },
  "distance": { "km": 399337, "au": 0.002669, "light_time_seconds": 1.28 },
  "constellation": "Leo",
  "constellation_precise": "Leo",
  "moonrise_and_set": {
    "next_moonrise": {"time": "2025-01-18 13:45:23 UTC", "azimuth_degrees": 78.3, "illumination_percent": 82.6},
    "next_moonset": {"time": "2025-01-19 02:12:45 UTC", "azimuth_degrees": 256.7, "illumination_percent": 82.6},
    "next_transit": {"time": "2025-01-18 20:00:00 UTC", "altitude_degrees": 60.1, "azimuth_degrees": 180.0, "illumination_percent": 82.6}
  },
  "viewing_conditions": {
    "atmospheric_extinction": 0.32,
    "extinction_effect": "32.0% dimming",
    "best_viewing_time": "Around transit (highest altitude)"
  },
  "libration": { "longitude_degrees": 2.1, "latitude_degrees": 1.3, "position_angle_degrees": 32.5, "note": "Simplified optical libration approximation" },
  "observer": { "latitude": 35.7478, "longitude": -95.3697, "geodetic_height": 0, "reference_frame": "WGS84" },
  "timestamp": "2025-01-18 02:59:09 UTC",
  "time_scales": {
    "utc": "2025-01-18 02:59:09 UTC",
    "tt": "2025-01-18 02:59:41 TT",
    "tdb": "2025-01-18 02:59:41 TDB"
  },
  "precision": {
    "position_uncertainty_arcsec": 0.01,
    "time_system": "TDB",
    "reference_frame": "ICRS",
    "ephemeris": "de440.bsp"
  },
  "calculation_metadata": {
    "libraries_used": ["ephem", "skyfield", "astropy"],
    "ephemeris_used": "de440.bsp",
    "nutation_correction_applied": true,
    "aberration_correction_applied": true,
    "topocentric_correction_applied": true,
    "api_version": "1.1.0"
  }
}
```

### Example Mars Response

```json
{
  "name": "mars",
  "position": {
    "altitude": { "degrees": 12.34, "radians": "0.215" },
    "azimuth": { "degrees": 101.23, "radians": "1.767" },
    "precise_altitude": 12.3412,
    "precise_azimuth": 101.2345
  },
  "celestial_coordinates": {
    "right_ascension": { "hours": 5.1234, "degrees": 76.851 },
    "declination": { "degrees": 23.4567 }
  },
  "distance": { "km": 225000000, "au": 1.504 },
  "constellation": "Gemini",
  "constellation_precise": "Gemini",
  "marsrise_and_set": {
    "next_marsrise": "2025-01-18 15:12:00 UTC",
    "next_marset": "2025-01-19 03:45:00 UTC"
  },
  "viewing_conditions": {
    "atmospheric_extinction": "Calculated based on altitude",
    "best_viewing_time": "Based on maximum altitude"
  },
  "observer": { "latitude": 35.7478, "longitude": -95.3697 },
  "timestamp": "2025-01-18 02:59:09 UTC"
}
```

## Response Fields

- `name`: The celestial body name
- `position`: Position in the sky from observer's perspective
  - `altitude`: Angular height above the horizon (negative values mean below horizon)
  - `azimuth`: Direction along the horizon (0° = North, 90° = East, etc.)
  - `precise_altitude/azimuth`: Higher precision values from skyfield (if location provided)
- `celestial_coordinates`: Position in the celestial sphere
  - `right_ascension`: Position in hours (0-24) and degrees (0-360)
  - `declination`: Angular distance from the celestial equator
- `distance`: Distance from Earth in kilometers and astronomical units
- `constellation`: Current constellation the body is in
- `constellation_precise`: Constellation determined using astropy's more precise algorithms
- `viewing_conditions`: Information about visibility and optimal viewing
- `observer`: Location coordinates (only with location)
- `timestamp`: UTC timestamp of the observation
- **Moon only:**
  - `current_phase`, `next_phases`, `phase_precise`, `moonrise_and_set`, `libration`
- **Mars only:**
  - `marsrise_and_set`

## Code Structure & Extensibility

The codebase is modular and designed for easy expansion:

- Each celestial body is implemented as a class in the `celestial/` directory, subclassing a common `CelestialBody` base.
- Adding a new body (e.g., Jupiter) is as simple as creating a new class and registering a new endpoint in `function_app.py`.
- Shared logic lives in the base class or utility modules.
- The code is heavily commented for clarity and maintainability.

## Error Handling

The API includes validation for:

- Valid JSON input
- Latitude and longitude format (must be valid numbers)
- Latitude and longitude ranges (latitude: -90 to 90, longitude: -180 to 180)
- Graceful handling of calculation errors from each library

## Future Expansion

The API is designed to be easily expanded to support other celestial bodies:

- Add a new class in `celestial/` for the body (e.g., Jupiter, Saturn, Sun)
- Register a new endpoint in `function_app.py`
- Implement or override methods as needed for body-specific features

## Deployment

To deploy to Azure:

1. Create an Azure Function App in your Azure portal
2. Deploy using Azure Functions Core Tools:

```bash
func azure functionapp publish <your-function-app-name>
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
