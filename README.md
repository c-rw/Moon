# Celestial Bodies Information API

An Azure Function API that provides detailed information about celestial bodies, currently focusing on the Moon. This API uses multiple astronomical calculation libraries for enhanced precision and detailed information.

## Features

- **Current moon phase** (percentage illuminated)
- **Next new moon and full moon dates**
- **Precise positioning** (altitude, azimuth, right ascension, declination)
- **Distance from Earth** in kilometers and astronomical units
- **Current constellation** with multiple determination methods
- **Rise and set times** when location is provided
- **Advanced viewing conditions** including atmospheric information

## Libraries Used

The API leverages three powerful astronomical libraries:
- **`ephem`**: For basic planetary calculations, moon phase, and rise/set times
- **`skyfield`**: For precise astronomical positioning and distance calculations
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

## Usage

### Starting the API Locally

Run the API locally using Azure Functions Core Tools:

```bash
func start
```

The API will be available at `http://localhost:7071/api/moon`

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

Note: Latitude must be between -90 and 90, longitude between -180 and 180.

### Example Response

```json
{
  "name": "moon",
  "current_phase": 82.61,
  "next_phases": [
    {
      "phase": "New Moon",
      "date": "2025-01-29 12:35:54 UTC"
    },
    {
      "phase": "Full Moon",
      "date": "2025-02-12 13:53:19 UTC"
    }
  ],
  "position": {
    "altitude": {
      "degrees": -6.97,
      "radians": "-0:06:57.6"
    },
    "azimuth": {
      "degrees": 78.30,
      "radians": "78:18:12.0"
    },
    "precise_altitude": -6.9694,
    "precise_azimuth": 78.3033
  },
  "celestial_coordinates": {
    "right_ascension": {
      "hours": 10.8456,
      "degrees": 162.6840
    },
    "declination": {
      "degrees": 8.5723
    }
  },
  "distance": {
    "km": 399337,
    "au": 0.002669
  },
  "constellation": "Leo",
  "constellation_precise": "Leo",
  "phase_precise": 82.59,
  "moonrise_and_set": {
    "next_moonrise": "2025-01-18 13:45:23 UTC",
    "next_moonset": "2025-01-19 02:12:45 UTC"
  },
  "viewing_conditions": {
    "atmospheric_extinction": "Calculated based on altitude",
    "best_viewing_time": "Based on maximum altitude"
  },
  "libration": {
    "note": "Libration values available on request"
  },
  "observer": {
    "latitude": 35.7478,
    "longitude": -95.3697
  },
  "timestamp": "2025-01-18 02:59:09 UTC"
}
```

## Response Fields

- `name`: The celestial body name
- `current_phase`: Percentage of the moon's visible disk that is illuminated (0-100)
- `next_phases`: Upcoming new moon and full moon dates
- `position`: Position in the sky from observer's perspective
  - `altitude`: Angular height above the horizon (negative values mean below horizon)
  - `azimuth`: Direction along the horizon (0° = North, 90° = East, etc.)
  - `precise_altitude/azimuth`: Higher precision values from skyfield
- `celestial_coordinates`: Position in the celestial sphere
  - `right_ascension`: Position in hours (0-24) and degrees (0-360)
  - `declination`: Angular distance from the celestial equator
- `distance`: Distance from Earth in kilometers and astronomical units
- `constellation`: Current constellation the body is in
- `constellation_precise`: Constellation determined using astropy's more precise algorithms
- `phase_precise`: Moon phase calculated with higher precision
- `moonrise_and_set`: Next moonrise and moonset times (only with location)
- `viewing_conditions`: Information about visibility and optimal viewing
- `observer`: Location coordinates (only with location)
- `timestamp`: UTC timestamp of the observation

## Error Handling

The API includes validation for:
- Valid JSON input
- Latitude and longitude format (must be valid numbers)
- Latitude and longitude ranges (latitude: -90 to 90, longitude: -180 to 180)
- Graceful handling of calculation errors from each library

## Future Expansion

The API is designed to be expanded to support other celestial bodies:
- Mars
- Jupiter
- Other planets and objects in the solar system

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