# Powder Hound

An MCP (Model Context Protocol) server that finds the best ski resort snow conditions worldwide and searches for upcoming flights to get there.

## What It Does

Ask natural language questions like **"Where is the best snow right now?"** and get back:

- Ski resorts ranked by recent snowfall
- Current snow depth and weather conditions
- Wind speed data for snow quality assessment
- 7-day snow forecasts
- Upcoming flights from your departure city

## MCP Tools

| Tool | Description |
|------|-------------|
| `find_best_snow` | Ranks 2,200+ resorts worldwide by recent snowfall, forecast snowfall, or both combined. Filter by region and resort size. |
| `get_resort_conditions` | Detailed day-by-day snow, wind, and weather forecast for a specific resort. |
| `search_flights` | Search for upcoming flights from your airport to a resort's nearest airport. |
| `flight_info` | Get full details (departure time, arrival time, status) for a specific flight. |

## Resort Coverage

Resort data is fetched dynamically from OpenStreetMap, covering 2,200+ ski resorts worldwide. Small non-resort areas (tubing hills, sledding parks) and abandoned sites are filtered out. Each resort is automatically matched to its nearest major airport. Examples by region:

- **US** (~422 resorts) — Vail, Mammoth, Killington, and more
- **Japan** (~276 resorts) — Niseko, Hakuba, and more
- **France** (~217 resorts) — Chamonix, Val d'Isère, and more
- **Switzerland** (~201 resorts) — Saas Fee, Zermatt, and more
- **Austria** (~195 resorts) — St. Anton, Kitzbühel, and more
- **Italy** (~156 resorts) — Cortina d'Ampezzo, Courmayeur, Livigno, and more
- **Canada** (~142 resorts) — Whistler, Revelstoke, and more
- **Norway** (~77 resorts) — Trysil, Hemsedal, Kvitfjell, and more

Plus resorts in Germany, Sweden, Spain, New Zealand, Argentina, and many more countries.

## APIs Used

| API | Purpose | API Key Required? |
|-----|---------|-------------------|
| [Open-Meteo](https://open-meteo.com/) | Snow and weather data | No |
| [OpenStreetMap Overpass](https://overpass-api.de/) | Ski resort database | No |
| [AeroDataBox](https://aerodatabox.com/) (via RapidAPI) | Flight schedules and routes | Yes (free tier, 600 units/month) |

## Setup

### Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) package manager

### Install

```bash
git clone <repo-url>
cd Powder-Hound
uv sync
```

### Configure API Keys

Set your AeroDataBox API key as an environment variable or in a `.env` file:

```
AERODATABOX_API_KEY=your_rapidapi_key_here
```

Get a free key by subscribing to [AeroDataBox on RapidAPI](https://rapidapi.com/aedbx-aedbx/api/aerodatabox).

> Snow conditions work without any API key. The flight search requires an AeroDataBox key.

> **Free tier limitations:** 600 API units/month (not requests — endpoints cost 1-60 units each). Rate limited to 1 request/second. Future flight schedules available up to 365 days out but may show fewer results than day-of. Each flight search uses 2 calls (two 12-hour windows). No overages — once your monthly units are used, requests will fail until the next billing cycle. Only direct flights are returned — connecting itineraries are not currently supported.

### Run

**Development (MCP Inspector):**

```bash
uv run mcp dev src/main.py
```

**Install in Claude Desktop:**

```bash
uv run mcp install src/main.py
```

Or manually add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "powder-hound": {
      "command": "your_uv_path_here",
      "args": ["run", "--directory", "/path/to/Powder-Hound", "src/main.py"],
      "env": {
        "AERODATABOX_API_KEY": "your_rapidapi_key_here"
      }
    }
  }
}
```

## Example Queries

- "Where is the best snow right now?"
- "Which resorts in Japan got the most snow this week?"
- "What are conditions like at Whistler?"
- "Find me flights from SFO to ski resorts with fresh snow"
- "Best snow in Europe right now?"
