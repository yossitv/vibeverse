# Hack to Create - Project Submission Form (Draft)

> Fields marked with * are required.

---

## Project Name *

VibeVerse

---

## Submission Description *

VibeVerse is an AI-powered 3D asset generation pipeline for Roblox Studio — "Cursor for Game Crafting." Game creators describe what they need in natural language, and VibeVerse automatically generates candidate images, converts them into 3D models (GLB), optimizes the geometry, and exports production-ready assets directly into Roblox Studio. The system is built on NVIDIA's FastMCP framework with optional NemoClaw sandboxed agent execution, enabling a secure, modular, and extensible AI-driven content creation workflow. By reducing asset production from hours to minutes, VibeVerse empowers creators to focus on ideas rather than manual modeling.

---

## Demo Video *

<!-- TODO: Add demo video URL before submission -->

---

## List Team Members Names and Emails *

<!-- TODO: Fill in team member names and emails -->

---

## GitHub Repo *

https://github.com/yossitv/vibeverse

---

## Models Used *

- **NVIDIA Nemotron 3 Super 120B** (`nvidia/nemotron-3-super-120b-a12b`) — Agent reasoning and orchestration via NemoClaw sandboxed execution
- **NVIDIA Nemotron 3 Ultra 253B** (`nvidia/llama-3.1-nemotron-ultra-253b-v1`) — Available as an alternative high-capacity reasoning model
- **NVIDIA Nemotron 3 Nano 30B** (`nvidia/nemotron-3-nano-30b-a3b`) — Lightweight local inference option via vLLM
- **Google Gemini** (nano-banana-pro-preview) — Text-to-image candidate generation with prompt enhancement
- **Meshy AI** — Image-to-3D model conversion with PBR (Physically Based Rendering) support

---

## Tools Used *

- **NVIDIA FastMCP** — Model Context Protocol framework for tool and resource orchestration
- **NVIDIA NemoClaw** — Sandboxed autonomous AI agent toolkit for secure pipeline execution
- **NVIDIA OpenShell** — Secure container runtime with kernel-level isolation (Landlock, seccomp, network namespaces)
- **NVIDIA NIM** — Inference microservice for local model deployment
- **NVIDIA Cloud Inference** (build.nvidia.com) — Cloud-hosted Nemotron model inference
- **Gemini API** — Text-to-image generation
- **Meshy AI API** — Image-to-3D conversion with GLB output
- **Python / httpx / uvicorn** — Backend and async HTTP stack
- **Roblox Studio Plugin** — Direct asset placement into game environments

---

## What is the primary use case for your tool?

A Roblox game creator opens VibeVerse and types a natural language prompt — for example, "a glowing crystal sword with ice particles." Here's what happens next:

1. **Prompt Submission** — The creator submits the prompt via the REST API or MCP client. A job is created and enters the pipeline.
2. **AI Image Generation** — VibeVerse enhances the prompt (adding studio lighting, A-pose, white background directives) and sends it to the Gemini API, which generates multiple candidate images.
3. **3D Conversion** — The best candidate image is sent to Meshy AI, which converts the 2D image into a fully textured 3D model (GLB format) with PBR materials.
4. **Optimization** — The 3D model is optimized for real-time rendering — mesh decimation, texture compression, and polygon budget enforcement ensure smooth performance in Roblox.
5. **Export & Placement** — The optimized GLB model is bundled with JSON metadata (tags, dimensions, material info) and exported. The creator places the asset directly into Roblox Studio via the plugin.
6. **Iteration** — If the creator wants refinements, they can re-prompt or use NemoClaw's agent loop for autonomous iterative improvements.

The entire workflow — from text prompt to placed 3D asset — takes minutes instead of hours. Creators strike gold by spending their time on game design and storytelling, not manual 3D modeling.

---

## Describe anything used from the NVIDIA AI ecosystem

VibeVerse leverages the NVIDIA AI ecosystem extensively:

- **FastMCP (Model Context Protocol)** — The entire MCP server is built on FastMCP >= 2.0.0, which provides declarative tool and resource definitions for the asset generation pipeline. Each pipeline stage (image generation, 3D conversion, optimization, export) is exposed as an MCP tool.

- **NemoClaw** — Integrated as an optional sandboxed AI agent backend. NemoClaw enables autonomous multi-step pipeline execution with built-in safety guarantees. The agent can reason about asset quality, trigger re-generation, and manage complex workflows without human intervention.

- **OpenShell Runtime** — Provides kernel-level security isolation for NemoClaw agents using Landlock filesystem confinement, seccomp system call filtering, and network namespace policies. All agent execution is sandboxed to prevent unauthorized access.

- **NVIDIA Cloud Inference** — Nemotron 3 models are accessed via `integrate.api.nvidia.com` for agent reasoning. The blueprint supports multiple inference profiles: NVIDIA Cloud, NCP, local NIM, and vLLM backends.

- **NVIDIA NIM** — Configured as an optional local inference microservice (`http://nim-service.local:8000/v1`) for on-premise deployment of Nemotron models without cloud dependency.

- **Nemotron Model Family** — The system is configured to use Nemotron 3 Super 120B as the primary reasoning model, with fallback options including Ultra 253B, Super 49B, and Nano 30B depending on deployment constraints.

- **DGX Spark** — Documented as a deployment target for scaling the inference pipeline, with 42 reference playbooks available for broader NVIDIA ecosystem integration.
