# VibeVerse Roblox Plugin

`VibeVersePlugin.lua` is a Roblox Studio plugin script for the MVP flow described in [storming.md](/Users/ys/Documents/GitHub/vibeverse/docs/storming.md).

What it does:

- Creates a Studio toolbar button and docked widget
- Sends prompts to the local backend with `POST /api/jobs`
- Polls `/status`, `/chat`, and `/asset`
- Shows merged chat and pipeline events inside Studio
- Places a proxy model into `Workspace` when a job reaches `exported`
- Marks the backend job as `placed`

## Why It Places a Proxy

The current backend exports a local filesystem path to the generated OBJ. Roblox plugins cannot reliably ingest that path directly in Studio without an additional import or upload step, so this MVP places a proxy model with metadata attached.

The placed model includes:

- `Attributes` with job ID, asset ID, prompt, export path, and metadata path
- A `Configuration` folder with the same metadata as `StringValue`s
- A colored placeholder `Part` so the end-to-end flow can be demoed in Studio

## Install In Studio

1. Start the backend:

```bash
python3 -m backend.api.server --host 127.0.0.1 --port 8000
```

2. Open Roblox Studio.
3. Create a new local plugin script.
4. Paste the contents of [VibeVersePlugin.lua](/Users/ys/Documents/GitHub/vibeverse/plugin/roblox/VibeVersePlugin.lua) into that script.
5. Enable the plugin.
6. Open the `VibeVerse` toolbar button.
7. Confirm the backend URL is `http://127.0.0.1:8000`.

## Demo Flow

1. Enter a prompt such as `create an Nvidia-themed event prop for Roblox`.
2. Click `Generate Asset`.
3. Wait until the status becomes `exported`.
4. Click `Place In Studio`.
5. Inspect the created model in `Workspace`.

## Future Upgrade Path

To place the actual generated mesh instead of a proxy, the backend needs to expose a plugin-consumable import path, for example:

- an uploaded Roblox asset ID
- a Studio-importable URL
- a plugin-side import bridge that can read the generated model data
