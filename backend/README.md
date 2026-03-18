# VibeVerse Backend API

`docs/idea.md` の MVP 要件に合わせた、ローカル JSON 保存ベースの最小バックエンドです。

実装しているもの:

- ジョブ作成 API
- ジョブ状態取得 API
- チャット / 処理ログ取得 API
- 生成アセット情報取得 API
- ローカル JSON への保存
- NemoClaw assistant request forwarding
- 擬似パイプライン
  - `generate_candidates`
  - `convert_to_3d`
  - `optimize_model`
  - `export_for_roblox`

## 起動

リポジトリルートで実行します。

```bash
python3 -m backend.api.server --host 127.0.0.1 --port 8000 --nemoclaw-sandbox my-assistant
```

## エンドポイント

- `GET /health`
- `GET /api/jobs`
- `POST /api/jobs`
- `GET /api/jobs/{job_id}`
- `GET /api/jobs/{job_id}/status`
- `GET /api/jobs/{job_id}/chat`
- `GET /api/jobs/{job_id}/asset`
- `POST /api/jobs/{job_id}/placed`

## curl 例

ジョブ作成:

```bash
curl -sS http://127.0.0.1:8000/api/jobs \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"create an Nvidia-themed event prop for Roblox"}'
```

NemoClaw assistant request:

```bash
curl -sS http://127.0.0.1:8000/api/jobs \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"say hello from NemoClaw","processor":"nemoclaw","sandbox_name":"my-assistant"}'
```

状態確認:

```bash
curl -sS http://127.0.0.1:8000/api/jobs/<job_id>/status
```

チャット / 進捗取得:

```bash
curl -sS http://127.0.0.1:8000/api/jobs/<job_id>/chat
```

アセット情報取得:

```bash
curl -sS http://127.0.0.1:8000/api/jobs/<job_id>/asset
```

Studio に配置済みとしてマーク:

```bash
curl -sS -X POST http://127.0.0.1:8000/api/jobs/<job_id>/placed
```

## 保存先

- セッション / ジョブ状態: `backend/jobs/sessions/`
- 生成アセット: `backend/jobs/projects/gtc_event_assets/assets/`
- アセット一覧: `backend/jobs/projects/gtc_event_assets/assets.json`

`processor=demo` のジョブは `queued -> running -> image_generated -> converted_to_3d -> optimized -> exported -> placed` の順で進みます。

`processor=nemoclaw` のジョブは `queued -> running -> completed` の順で進み、応答本文は `GET /api/jobs/{job_id}/chat` の `messages` と `assistant.response` で取得できます。
