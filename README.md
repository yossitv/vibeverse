# VibeVerse

Text prompt from Roblox Studio plugin to AI-generated 3D asset placement.

## Setup

### Prerequisites

- Python 3.12+
- [Gemini API Key](https://aistudio.google.com/apikey)
- [Meshy AI API Key](https://www.meshy.ai/)

### 1. API Keys

Create a `.env` file in the `mcp/` directory:

```bash
cp mcp/.env.example mcp/.env
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

### 2. Install & Run

```bash
cd mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the MCP server (stdio)
python server.py

# Or run with HTTP transport
fastmcp run server.py:mcp --transport http --port 8000
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `generate_candidates` | Generate candidate images from a text prompt |
| `convert_to_3d` | Convert a generated image into a 3D object (GLB) |
| `tag_asset` | Add metadata tags to a job's asset |
| `export_for_roblox` | Optimize and export for Roblox Studio |
| `get_job_status` | Check pipeline job status |
