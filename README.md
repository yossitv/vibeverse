# VibeVerse

Text prompt from Roblox Studio plugin to AI-generated 3D asset placement.

## Setup

### Prerequisites

- Python 3.12+
- [Gemini API Key](https://aistudio.google.com/apikey)
- [Meshy AI API Key](https://www.meshy.ai/)

### 1. API Keys

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Then fill in your keys:

```env
GEMINI_API_KEY=your_gemini_api_key_here
MESHY_API_KEY=your_meshy_api_key_here
```

#### How to get the keys

| Service | Where to get | Used for |
|---------|-------------|----------|
| **Gemini API** | [Google AI Studio](https://aistudio.google.com/apikey) - sign in and click "Create API Key" | Image generation (Nano Banana Pro) |
| **Meshy AI** | [Meshy Dashboard](https://www.meshy.ai/) - sign up, go to Settings > API Keys | Image-to-3D conversion, rigging |

### 2. Quick Start

```bash
./start.sh
```

This will:
1. Load `.env` from the project root
2. Create `.venv` at the project root (if not exists) and install dependencies
3. Start the Backend API on `http://127.0.0.1:8000`
4. Start the MCP Server on `http://127.0.0.1:8001`

Stop with `Ctrl+C`.

### Manual Start

```bash
# Backend API
python3 -m backend.api.server --host 127.0.0.1 --port 8000 --nemoclaw-sandbox my-assistant

# MCP Server (stdio)
cd mcp && python server.py

# MCP Server (HTTP)
cd mcp && fastmcp run server.py:mcp --transport http --port 8001
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `generate_candidates` | Generate candidate images from a text prompt |
| `convert_to_3d` | Convert a generated image into a 3D object (GLB) |
| `tag_asset` | Add metadata tags to a job's asset |
| `export_for_roblox` | Optimize and export for Roblox Studio |
| `get_job_status` | Check pipeline job status |

## NemoClaw Request Example

If `my-assistant` is running through NemoClaw, the backend can forward a request to it:

```bash
curl -sS http://127.0.0.1:8000/api/jobs \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"say hello from NemoClaw","processor":"nemoclaw","sandbox_name":"my-assistant"}'
```
