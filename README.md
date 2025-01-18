# Moon Information API

An Azure Function API that provides detailed information about the Moon's position, phase, and timing of astronomical events. Built using Python and the `ephem` library.

## Features

- Current moon phase (percentage illuminated)
- Next new moon and full moon dates
- Moon's current position (altitude and azimuth)
- Distance from Earth in kilometers
- Current constellation
- Moon rise and set times (when location provided)
- Location-specific calculations

## Prerequisites

- Python 3.10 or higher
- Azure Functions Core Tools
- Python Azure Functions dependencies

## Installation

1. Clone the repository:
```bash
git clone [your-repository-url]
cd moon
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install azure-functions
pip install ephem
```

## Usage

### Starting the API Locally

Run the API locally using Azure Functions Core Tools:
```bash
func start
```

The API will be available at `http://localhost:7071/api/moon`

### API Endpoints

#### Basic Moon Information
```bash
curl http://localhost:7071/api/moon
```

#### Location-Specific Moon Information
```bash
curl -X POST \
  http://localhost:7071/api/moon \
  -H "Content-Type: application/json" \
  -d '{"latitude": "35.7478", "longitude": "-95.3697"}'
```

### Example Response

```json
{
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
  "altitude": "-6:57:58.6",
  "azimuth": "78:18:12.0",
  "distance": "399337 km",
  "constellation": "Leo",
  "moonrise_and_set": {
    "next_moonrise": "2025-01-18 13:45:23 UTC",
    "next_moonset": "2025-01-19 02:12:45 UTC"
  },
  "observer": {
    "latitude": "35.7478",
    "longitude": "-95.3697",
    "timestamp": "2025-01-18 02:59:09 UTC"
  }
}
```

## Response Fields

- `current_phase`: Percentage of the moon's visible disk that is illuminated (0-100)
- `next_phases`: Upcoming new moon and full moon dates
- `altitude`: Angular height above the horizon (negative values mean below horizon)
- `azimuth`: Direction along the horizon (0° = North, 90° = East, etc.)
- `distance`: Distance from Earth in kilometers
- `constellation`: Current constellation the moon is in
- `moonrise_and_set`: Next moonrise and moonset times (only included when location provided)
- `observer`: Location and timestamp of the observation

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