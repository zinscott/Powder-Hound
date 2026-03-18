# Powder Hound

An MCP (Model Context Protocol) server that finds the best ski resort snow conditions worldwide and searches for upcoming flights to get there.

## What It Does

Ask natural language questions like **"Where is the best snow right now?"** and get back:

- Ski resorts ranked by recent snowfall
- Current snow depth and weather conditions
- 7-day snow forecasts
- Upcoming flights from your departure city

## MCP Tools

| Tool | Description |
|------|-------------|
| `find_best_snow` | Ranks ~35 resorts worldwide by recent snowfall. Optionally finds upcoming flights from your airport. |
| `get_resort_conditions` | Detailed day-by-day snow and weather forecast for a specific resort. |
| `search_flights` | Search for upcoming flights between any two airports. |

## Resort Coverage

- **US Rockies** — Vail, Alta, Jackson Hole, Aspen, Steamboat, Park City, Snowbird, Big Sky, and more
- **US Pacific** — Mammoth, Palisades Tahoe, Heavenly, Mt. Bachelor, Crystal Mountain
- **US Northeast** — Killington, Stowe, Jay Peak, Sunday River, Sugarloaf
- **Canada** — Whistler, Revelstoke, Kicking Horse, Banff/Lake Louise, Mont Tremblant
- **Europe** — Chamonix, Zermatt, Verbier, St. Anton, Val d'Isere, Cortina
- **Japan** — Niseko, Hakuba

## APIs Used

| API | Purpose | API Key Required? |
|-----|---------|-------------------|
| [Open-Meteo](https://open-meteo.com/) | Snow and weather data | No |
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
AVIATION_STACK_API_KEY=your_api_key_here
```

Get a free key at [aviationstack.com](https://aviationstack.com/).

> Snow conditions work without any API key. The flight search requires an Aviation Stack key.

### Run

**Development (MCP Inspector):**

```bash
uv run mcp dev main.py
```

**Install in Claude Desktop:**

```bash
uv run mcp install main.py
```

Or manually add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "powder-hound": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/Powder-Hound", "main.py"],
      "env": {
        "AVIATION_STACK_API_KEY": "your_key_here"
      }
    }
  }
}
```

## Example Queries

- "Where is the best snow right now?"
- "Which resorts in Colorado got the most snow this week?"
- "What are conditions like at Whistler?"
- "Find me flights from SFO to ski resorts with fresh snow"
