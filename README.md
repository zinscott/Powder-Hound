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
| `find_best_snow` | Ranks 3,500+ resorts worldwide by recent snowfall. Filter by region and optionally find upcoming flights. |
| `get_resort_conditions` | Detailed day-by-day snow, wind, and weather forecast for a specific resort. |
| `search_flights` | Search for upcoming flights between any two airports. |

## Resort Coverage

Resort data is fetched dynamically from OpenStreetMap, covering 3,500+ ski areas worldwide. Each resort is automatically matched to its nearest major airport. Examples by region:

- **US** (~588 resorts) — Vail, Mammoth, Killington, and more
- **Japan** (~423 resorts) — Niseko, Hakuba, and more
- **Switzerland** (~276 resorts) — Saas Fee, Zermatt, and more
- **Austria** (~260 resorts) — St. Anton, Kitzbühel, and more
- **France** (~234 resorts) — Chamonix, Val d'Isère, and more
- **Norway** (~204 resorts)
- **Italy** (~199 resorts)
- **Canada** (~190 resorts) — Whistler, Revelstoke, and more

Plus resorts in Germany, Sweden, Spain, New Zealand, Argentina, and many more countries.

## APIs Used

| API | Purpose | API Key Required? |
|-----|---------|-------------------|
| [Open-Meteo](https://open-meteo.com/) | Snow and weather data | No |
| [OpenStreetMap Overpass](https://overpass-api.de/) | Ski resort database | No |
| [Aviation Stack](https://aviationstack.com/) | Flight schedules and routes | Yes (free tier, 100 req/month) |

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

Set your Aviation Stack API key as an environment variable or in a `.env` file:

```
AVIATIONSTACK_API_KEY=your_api_key_here
```

Get a free key at [aviationstack.com](https://aviationstack.com/).

> Snow conditions work without any API key. The flight search requires an Aviation Stack key.

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
      "command": "uv",
      "args": ["run", "--directory", "/path/to/Powder-Hound", "src/main.py"],
      "env": {
        "AVIATIONSTACK_API_KEY": "your_key_here"
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
