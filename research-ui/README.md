# Research Pipeline UI

Frontend for your multi-agent research pipeline (search → reader → writer → critic).

## 1. Start the backend

In your Python project folder (where `agents.py`, `pipeline.py`, `.env` live), add `api_server.py`
(provided separately), then:

```bash
pip install fastapi "uvicorn[standard]"
uvicorn api_server:app --reload --port 8000
```

Check it's alive at http://127.0.0.1:8000/api/health — you should see `{"status":"ok"}`.
(Visiting http://127.0.0.1:8000/ itself will 404 — that's expected, it's an API, not a webpage.)

## 2. Start this frontend

In this folder:

```bash
npm install
npm run dev
```

Then open the URL it prints — usually http://localhost:5173.

## Features

This UI includes:

- live multi-stage pipeline status for search → reader → writer → critic
- a separate document chat for normal conversations, web pages, and text-based PDFs
- advisory copyright/license indicator and safety keyword checks for loaded sources
- source list display for discovered URLs
- copy-to-clipboard support for the final research report
- download-as-text export for saved research notes
- environment-based backend configuration for local and deployed setups

## Configuration

The UI uses the `VITE_API_BASE` environment variable for the backend URL.

Create a `.env` file in this folder with:

```bash
VITE_API_BASE=http://localhost:8000
```

If you do not set it, the app falls back to `http://localhost:8000` automatically.

## Document chat notes

- PDF uploads are limited to 8 MB and 100 pages. Scanned PDFs that contain no selectable text need OCR, which is not included.
- URL loading supports public HTTP/HTTPS web pages and PDF links; local/private-network URLs and redirects are rejected.
- Copyright checks only look for common notice/license wording. A missing notice is not permission to reuse content, and these checks are not legal advice.
- Safety checks are advisory keyword scans. They can miss unsafe content or flag benign content and do not block messages.
- Chat requests are sent to the configured model provider through the backend.
