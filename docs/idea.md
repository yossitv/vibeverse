VibeVerse— Cursor for Game Crafting

Elevator Pitch
I’m a game creator with 160,000 downloads on Minecraft.
But I couldn’t ship my next game because asset creation took too long.

So we built VibeVerse — Cursor for Game Crafting.

An AI agent that turns hours of asset creation into minutes,
and works directly inside Roblox.

Pitch
---
👉 VibeVerse — Cursor for Game Crafting

🧠 Story

I’m a game creator.
My Minecraft project reached over 160,000 downloads.

But I realized something frustrating.

I didn’t spend my time designing gameplay.
I spent most of my time crafting assets.

And because of that, I couldn’t ship my next game.

💥 Problem

Game creators are not limited by ideas.
They are limited by asset production.

Instead of building experiences,
they spend hours crafting assets.

🚀 Solution

So we built VibeVerse — Cursor for Game Crafting.

An AI agent that helps creators generate, convert, and manage 3D assets in minutes.

Turning hours of crafting into minutes.

🎮 Demo導線

You describe what you want,
select from generated options,
and instantly turn them into usable 3D assets.

🔥 Roblox（強く短く）

We also built a Roblox plugin,
so creators can instantly use generated assets in real games.
[https://ir.roblox.com/financials/quarterly-results/default.aspx](https://about.roblox.com/ja/ja-newsroom/2025/09/roblox-annual-economic-impact-report)

🧠 Vision

We’re not just generating assets.

We’re building a new way to create games.

---



```pipline
Roblox Plugin
   ↓
Backend API
   ├─ Session / Job DB (json ステータスを見れるようにして、評価しやすくする)
   ├─ Secret manager or env vars
   ├─ File/Object storage
   └─ LLM agent
          ↓
        MCP client
          ↓
        MCP server
          ├─ generate_candidates
          ├─ convert_to_3d
          ├─ tag_asset
          └─ export_for_roblox
```

```dir
project/
├─ backend/
│  ├─ api/
│  ├─ agent/
│  ├─ services/
│  ├─ jobs/
│  │  ├─ sessions/
│  │  │  ├─ sess_xxx.json
│  │  │  └─ sess_yyy.json
│  │  └─ projects/
│  │     ├─ <gtc_event_assets>/ #デモのため、今回は場所固定
│  │     │  ├─ assets.json
│  │     │  └─ assets/
│  │     │     ├─ asset_001/
│  │     │     │  ├─ preview.png
│  │     │     │  ├─ model.glb
│  │     │     │  └─ meta.json
│  │     │     └─ asset_002/
│  └─ db/
│
├─ mcp/
│  ├─ server/
│  ├─ tools/
│  │  ├─ generate_candidates.py
│  │  ├─ convert_to_3d.py
│  │  ├─ tag_asset.py
│  │  └─ export_for_roblox.py
│  └─ resources/
│
├─ plugin/
│  └─ roblox/
```

簡易的フロー
instraction->画像生成→Obj->モデル最適化-> (objデータ最適化) -> 環境に埋め込み


機能3dオブジェクトを作成して、管理できるパイプライン
backendサーバーとやりとりできる状態
mcpサーバーでtoolとして機能を呼び出せる状態
toolが正しく動いてる状態 
AIとチャットしながら対応する状態をcurlで引ける
pluginとして apiと繋げて、 agentのuiとして robloxで使える状態　Plugin api　luna でchat画面のuiを実装する


tool要件
画像生成
in 作りたいモデルの画像の prompt
out 出来上がった画像の保存dir

画像からobj作成
in 出来上がった画像のdir (or base 64)
out 出来上がったobjのdir (gltf? loblox?)

objの最適化
in 出来上がったobjのdir
out 出来上がったobjのdir

obj保存先の保持




時間があったら、


使うモデルをgt10で回す
データの差分をgit みたいに管理できる状態
動き作成　script api　アセットの差分




plugin
agent と会話して


demo 
nvidiaの画像から、イベント用のobjを作る


