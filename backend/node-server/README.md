# Node.js Backend Server

Realtime WebSocket backend for the React ADAS dashboard.

This server exposes the streams expected by `frontend/src/services/realtime.js`:

```text
/ws/video
/ws/lane
/ws/traffic-sign
/ws/warning
```

It also exposes:

```text
GET /api/health
GET /api/realtime/snapshot
```

## Run

From the project root:

```bash
npm run dev
```

Or run only this backend:

```bash
cd backend/node-server
npm start
```

The implementation uses only built-in Node.js modules, so no backend npm install is required.

## Notes

This server completes the realtime dashboard integration contract. It streams synchronized camera, lane, traffic sign and warning payloads to the frontend. The heavier Python model inference code remains in `backend/ai-service/` and the Streamlit demo at project root.
