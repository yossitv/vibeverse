# VibeVerse MVP Requirements

## 1. Purpose

VibeVerse is an internal demo MVP for Roblox asset creation.

The goal is to let a user enter a text prompt, generate an image from that prompt, convert the image into a static 3D object, and place the result into Roblox Studio through a plugin.

## 2. MVP Goal

The MVP must prove this end-to-end flow:

1. A user enters a prompt.
2. The system generates an image.
3. The system converts the image into a 3D object.
4. The system optimizes and exports the object into a Roblox-usable format.
5. The Roblox plugin places the asset into Studio.

## 3. Target User

The target user is the internal team running the demo.

This MVP is not for public release.

## 4. Scope

### 4.1 In Scope

- Internal demo only
- Static 3D objects only
- Roblox plugin UI for chat and prompt input
- Backend API connected to the plugin
- MCP server with callable tools
- Local file storage for sessions, jobs, assets, and metadata
- End-to-end asset pipeline from prompt to Roblox Studio placement
- Status retrieval through API and `curl`

### 4.2 Out of Scope

- Public product release
- Multi-user support
- Authentication and billing
- Cloud database or production object storage
- Asset marketplace publishing
- Animation, rigging, motion, or scripts
- Asset version diffing

## 5. Success Criteria

The MVP is successful if all of the following are true:

- A user can enter a prompt from the Roblox plugin.
- The backend generates at least one image from the prompt.
- The backend converts the generated image into a static 3D object.
- The backend saves the generated files and metadata locally.
- The backend exports the result in a format usable by Roblox Studio.
- The plugin can place the generated asset into Studio.
- The pipeline status can be checked from the backend API and through `curl`.

## 6. Functional Requirements

### 6.1 Prompt Input

- The system must accept a natural language prompt from the Roblox plugin.
- The system must also allow the same request flow to be triggered through the backend API.

### 6.2 Session and Job Tracking

- The backend must create a session or job record for each request.
- Each job must store its current status in local JSON files.
- Job status should be easy to inspect for debugging and demo evaluation.

Suggested states:

- `queued`
- `running`
- `image_generated`
- `converted_to_3d`
- `optimized`
- `exported`
- `placed`
- `failed`

### 6.3 Image Generation

- The system must generate one or more candidate images from the input prompt.
- The generated image files must be saved locally.
- The output of this step must include the saved file path or directory.

Input:

- Text prompt

Output:

- Generated image files
- Saved file paths

### 6.4 Image-to-3D Conversion

- The system must convert a generated image into a 3D object.
- The output must be stored locally.
- The conversion step may accept an image path or image data.

Input:

- Generated image path or image data

Output:

- 3D model file path

### 6.5 3D Optimization

- The system must run an optimization step on the generated 3D object.
- The optimized model must be saved locally as a separate usable output or final output.

Input:

- 3D model file path

Output:

- Optimized 3D model file path

### 6.6 Roblox Export

- The system must export the final 3D object in a format the Roblox plugin can use in Studio.
- The plugin must be able to import or place the asset into the current Studio environment.

### 6.7 Asset Storage

- The system must store generated assets locally.
- Each asset must have associated metadata.

Minimum metadata fields:

- Prompt
- Job ID
- Generated file paths
- Creation timestamp
- Status

### 6.8 MCP Tool Access

- The MCP server must expose the asset pipeline steps as tools.
- The following tools must exist.
- `generate_candidates`
- `convert_to_3d`
- `tag_asset`
- `export_for_roblox`
- Each tool must be callable and return a usable result for the next step.

### 6.9 API and Chat Access

- The backend API must support communication from the Roblox plugin.
- The backend must expose enough API endpoints to support the demo.

Minimum endpoint capabilities:

- Create a request
- Check job status
- Fetch chat or processing state
- Fetch generated asset information
- The same status and progress information must be retrievable through `curl`.

## 7. Non-Functional Requirements

### 7.1 Simplicity

- The MVP should favor simple implementation over production-grade architecture.
- Local JSON files and local directories are acceptable as the primary storage method.

### 7.2 Debuggability

- Pipeline progress must be visible from saved files and API responses.
- Failures must be easy to inspect during the demo.

### 7.3 Reliability for Demo

- The system only needs to support internal demo usage.
- It does not need to support high concurrency.

## 8. Suggested System Structure

```text
project/
├─ backend/
│  ├─ api/
│  ├─ agent/
│  ├─ services/
│  ├─ jobs/
│  │  ├─ sessions/
│  │  └─ projects/
│  └─ storage/
├─ mcp/
│  ├─ server/
│  ├─ tools/
│  └─ resources/
└─ plugin/
   └─ roblox/
```

## 9. End-to-End Demo Flow

1. The user opens the Roblox plugin.
2. The user enters a prompt for a desired object.
3. The plugin sends the request to the backend API.
4. The backend starts a job and stores job state locally.
5. The image generation tool creates candidate image output.
6. The 3D conversion tool creates a 3D object from the image.
7. The optimization step prepares the object for Roblox use.
8. The export step prepares the final output for Roblox Studio.
9. The plugin places the asset into Studio.
10. The user or operator can inspect job status through the API or `curl`.

## 10. Demo Example

Example demo scenario:

- Input prompt: create an event prop based on an Nvidia-themed image
- Output: a static 3D object that can be placed in Roblox Studio through the plugin
