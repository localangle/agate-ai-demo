# Agate UI

React + Vite frontend for the Agate demo. Calls the Agate API (`VITE_API_BASE`, default `http://localhost:8000`). **No auth** in this demo.

## Local (Docker)

From repo root:

```bash
make up
```

UI: http://localhost:5173

## Local (UI only)

Requires the API running and Node dependencies installed:

```bash
cd apps/agate-ui
npm install
node scripts/sync-nodes.js
npm run dev
```

## Node registry

After changing nodes under `packages/agate/src/agate_nodes/`:

```bash
node scripts/sync-nodes.js
```

## Production build

```bash
npm install
VITE_API_BASE=https://your-api.example.com npm run build
```

Serve the `dist/` output with any static host; ensure CORS on the API allows your UI origin.
