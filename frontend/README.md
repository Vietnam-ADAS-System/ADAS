# Frontend - Vietnam ADAS System

React/Vite dashboard for realtime ADAS visualization.

## Implemented Dashboard Modules

- TV1 Camera Streaming: render latest video frame, FPS, frame ID, connection state, loading and reconnect.
- TV3 Lane Visualization: lane boundary, lane center, safe zone, vehicle center, offset and lane warning overlay.
- TV4 Traffic Sign Visualization: bounding box, label, confidence, icon, active rule and priority highlight.
- TV5 Warning Panel: current warning, priority, system status and recent warning history.

The frontend only visualizes backend output. It does not run YOLO, DeepLab, DeepSORT, lane geometry calculation or warning decision logic.

## Structure

- `src/pages/Dashboard.jsx` - integrated realtime dashboard.
- `src/components/Camera/` - TV1 camera stream and canvas rendering.
- `src/components/Lane/` - TV3 lane overlay.
- `src/components/TrafficSign/` - TV4 traffic sign overlay.
- `src/components/Warning/` - TV5 warning panel.
- `src/services/realtime.js` - WebSocket connection, reconnect and message normalization helpers.

## Run

```bash
npm install
npm run dev
```

Local URL:

```text
http://localhost:5173/
```

Production build:

```bash
npm run build
```

## Backend WebSocket Contracts

By default, running from `frontend/` starts local demo mode, so it does not keep retrying backend WebSockets while the backend is offline.

To run the connected dashboard, start from the project root:

```bash
npm run dev
```

This starts:

- `backend/node-server` on port `3000`, serving the built React dashboard and realtime WebSockets
- Streamlit AI/model demo on port `8501`

Expected streams:

```text
/ws/video
/ws/lane
/ws/traffic-sign
/ws/warning
```

Enable backend streams manually when the Node server is already running:

```bash
VITE_API_PROXY_TARGET=http://127.0.0.1:3000 VITE_ENABLE_BACKEND_WS=true npm run dev
```

Or connect directly to a WebSocket backend:

```bash
VITE_WS_BASE_URL=ws://127.0.0.1:3000 npm run dev
```

If the backend is not available, the dashboard uses a local demo camera/overlay stream so the UI can still be tested.
