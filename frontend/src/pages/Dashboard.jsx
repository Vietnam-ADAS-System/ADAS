import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from "react";
import CameraView from "../components/Camera/CameraView.jsx";
import {
  createLaneDataStream,
  getDemoLaneVisualization,
} from "../components/Lane/lane.service.js";
import {
  createTrafficSignStream,
  createMockTrafficSignStream,
} from "../components/TrafficSign/traffic_sign.service.js";
import WarningPanel from "../components/Warning/WarningPanel.jsx";
import {
  createWarningStream,
  deriveDemoWarningData,
} from "../components/Warning/warning.service.js";
import { createPedestrianDataStream } from "../components/Pedestrian/pedestrian.service.js";
import { createVehicleDataStream, normalizeVehicleData } from "../components/Vehicle/vehicle.service.js";
import { useTheme } from "../services/theme.jsx";
import { useI18n, LANGUAGES, LANGUAGE_NAMES } from "../services/i18n.jsx";
import { createMockVehicleStream } from "../components/Vehicle/vehicle.service.js";
import { createMockPedestrianStream } from "../components/Pedestrian/pedestrian.service.js";
import { useVehicleControl } from "../hooks/useVehicleControl.js";

// Lazy load overlay components (now with real sprite rendering)
const PedestrianLayer = lazy(() => import("../components/Pedestrian/PedestrianLayer.jsx"));
const VehicleLayer = lazy(() => import("../components/Vehicle/VehicleLayer.jsx"));
const LaneLayer = lazy(() => import("../components/Lane/LaneLayer.jsx"));
const TrafficSignLayer = lazy(() => import("../components/TrafficSign/TrafficSignLayer.jsx"));

function isConnected(connection) {
  return connection?.state === "connected";
}

function isSameFrame(payload, frameId) {
  return payload?.frame_id != null && Number(payload.frame_id) === Number(frameId);
}

function filterSignsForFrame(signs, frameId) {
  return (signs || []).filter((sign) => isSameFrame(sign, frameId));
}

function selectLaneData({ backendData, connection, frameId, frameSize, vehicleState }) {
  if (isConnected(connection)) {
    return isSameFrame(backendData, frameId) ? backendData : null;
  }
  return frameId ? getDemoLaneVisualization(frameId, frameSize, vehicleState) : null;
}

function selectTrafficSigns({ backendData, connection, frameId, frameSize }) {
  if (isConnected(connection)) {
    return filterSignsForFrame(backendData, frameId);
  }
  return frameId ? createMockTrafficSignStream(frameId) : [];
}

function selectWarningData({ backendData, connection, frameId, laneData, trafficSigns, cameraConnection, vehicleState }) {
  if (isConnected(connection)) {
    return isSameFrame(backendData, frameId) ? backendData : null;
  }
  return frameId ? deriveDemoWarningData({ frameId, laneData, trafficSigns, cameraConnection, vehicleState }) : null;
}

function selectVehicleData({ backendData, connection, frameId }) {
  if (isConnected(connection)) {
    return isSameFrame(backendData, frameId) ? backendData : null;
  }
  return frameId ? createMockVehicleStream(frameId) : null;
}

function selectPedestrianData({ backendData, connection, frameId }) {
  if (isConnected(connection)) {
    return isSameFrame(backendData, frameId) ? backendData : null;
  }
  return frameId ? createMockPedestrianStream(frameId) : null;
}

function readableWarningType(type, t) {
  const labels = {
    SYSTEM: t('warning.system'),
    LANE_DEPARTURE: t('warning.lane_departure'),
    TRAFFIC_SIGN: t('warning.traffic_sign'),
    VEHICLE_NEARBY: t('warning.vehicle_nearby'),
    PEDESTRIAN: t('warning.pedestrian'),
  };
  return labels[type] || String(type || "SYSTEM").replaceAll("_", " ");
}

function readableLaneStatus(status, t) {
  const labels = {
    SAFE: t('lane.safe'),
    NEAR_BOUNDARY: t('lane.near_boundary'),
    LANE_DEPARTURE: t('lane.departure'),
    WAITING: t('lane.waiting'),
    Waiting: t('lane.waiting'),
  };
  return labels[status] || String(status || "WAITING").replaceAll("_", " ");
}

function readableSignStatus(status, t) {
  const labels = {
    "Speed Limit 40": t('sign.speed_40'),
    "No active sign warning": t('warning.no_active'),
    Waiting: t('lane.waiting'),
    Scanning: "Đang quét",
  };
  return labels[status] || status || "Đang quét";
}

function getAssistState(warningData, laneData, trafficSigns, t) {
  if (warningData?.active) {
    const level = warningData.warning_level || "MEDIUM";
    return {
      tone: level === "CRITICAL" || level === "HIGH" ? "danger" : "caution",
      title: readableWarningType(warningData.warning_type, t),
      message: warningData.warning_message || t('msg.driver_attention'),
    };
  }
  const laneStatus = laneData?.lane_status || warningData?.lane_status;
  if (laneStatus && laneStatus !== "SAFE") {
    return { tone: "caution", title: readableLaneStatus(laneStatus, t), message: t('msg.keep_center') };
  }
  return { tone: "safe", title: t('assist.ready'), message: t('assist.monitoring') };
}

function ChannelStatus({ label, connection, t }) {
  const state = connection?.state || "connecting";
  const labelByState = {
    connected: t('status.connected'),
    connecting: t('status.connecting'),
    reconnecting: t('status.reconnecting'),
    disconnected: t('status.disconnected'),
    demo: t('status.demo'),
    message_error: t('status.error'),
  };
  return (
    <div className={`channel-status channel-status--${state}`}>
      <span className="channel-status__dot" aria-hidden="true" />
      <span>{label}</span>
      <strong>{labelByState[state] || state}</strong>
    </div>
  );
}

function LanguageSelector({ language, setLanguage, t }) {
  return (
    <div className="language-selector">
      <select value={language} onChange={(e) => setLanguage(e.target.value)} aria-label={t('action.change_language')}>
        {Object.entries(LANGUAGE_NAMES).map(([code, name]) => (
          <option key={code} value={code}>{name}</option>
        ))}
      </select>
    </div>
  );
}

function ThemeToggle({ isDark, toggleTheme, t }) {
  return (
    <button className="theme-toggle" onClick={toggleTheme} aria-label={t('action.toggle_theme')} title={isDark ? t('theme.light') : t('theme.dark')}>
      {isDark ? (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
          <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
        </svg>
      ) : (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
      )}
    </button>
  );
}

export default function Dashboard() {
  const { isDark, toggleTheme } = useTheme();
  const { language, setLanguage, t, languageNames } = useI18n();
  const vehicleState = useVehicleControl();

  const [frameContext, setFrameContext] = useState(null);
  const [cameraConnection, setCameraConnection] = useState({ state: "connecting" });
  const [laneConnection, setLaneConnection] = useState({ state: "connecting" });
  const [trafficSignConnection, setTrafficSignConnection] = useState({ state: "connecting" });
  const [warningConnection, setWarningConnection] = useState({ state: "connecting" });
  const [pedestrianConnection, setPedestrianConnection] = useState({ state: "connecting" });
  const [vehicleConnection, setVehicleConnection] = useState({ state: "connecting" });
  const [laneDataFromBackend, setLaneDataFromBackend] = useState(null);
  const [trafficSignsFromBackend, setTrafficSignsFromBackend] = useState([]);
  const [warningDataFromBackend, setWarningDataFromBackend] = useState(null);
  const [pedestrianDataFromBackend, setPedestrianDataFromBackend] = useState(null);
  const [vehicleDataFromBackend, setVehicleDataFromBackend] = useState(null);

  useEffect(() => {
    const streams = [
      createLaneDataStream({ onData: setLaneDataFromBackend, onStatus: setLaneConnection }),
      createTrafficSignStream({ onData: setTrafficSignsFromBackend, onStatus: setTrafficSignConnection }),
      createWarningStream({ onData: setWarningDataFromBackend, onStatus: setWarningConnection }),
      createPedestrianDataStream({ onData: setPedestrianDataFromBackend, onStatus: setPedestrianConnection }),
      createVehicleDataStream({ onData: setVehicleDataFromBackend, onStatus: setVehicleConnection }),
    ];
    streams.forEach((s) => s.start());
    return () => streams.forEach((s) => s.stop());
  }, []);

  const frameId = frameContext?.frameId ?? null;
  const frameSize = frameContext?.frameSize;

  const laneData = useMemo(() => selectLaneData({ backendData: laneDataFromBackend, connection: laneConnection, frameId, frameSize, vehicleState }), [frameId, frameSize, laneConnection, laneDataFromBackend, vehicleState]);
  const trafficSigns = useMemo(() => selectTrafficSigns({ backendData: trafficSignsFromBackend, connection: trafficSignConnection, frameId, frameSize }), [frameId, frameSize, trafficSignConnection, trafficSignsFromBackend]);
  const vehicleData = useMemo(() => selectVehicleData({ backendData: vehicleDataFromBackend, connection: vehicleConnection, frameId }), [frameId, vehicleConnection, vehicleDataFromBackend]);
  const pedestrianData = useMemo(() => selectPedestrianData({ backendData: pedestrianDataFromBackend, connection: pedestrianConnection, frameId }), [frameId, pedestrianConnection, pedestrianDataFromBackend]);
  const warningData = useMemo(() => selectWarningData({ backendData: warningDataFromBackend, connection: warningConnection, frameId, laneData, trafficSigns, cameraConnection, vehicleState }), [cameraConnection, frameId, laneData, trafficSigns, warningConnection, warningDataFromBackend, vehicleState]);
  const assistState = useMemo(() => getAssistState(warningData, laneData, trafficSigns, t), [laneData, trafficSigns, warningData, t]);

  const handleFrameChange = useCallback((nextFrameContext) => setFrameContext(nextFrameContext), []);

  const renderOverlays = useCallback(
    ({ frameId: overlayFrameId, frameSize: overlayFrameSize, viewport, connection }) => {
      const effectiveFrameSize = overlayFrameSize || frameSize;
      const isRealMode = isConnected(connection);

      // Get data based on mode
      const overlayLaneData = selectLaneData({ backendData: laneDataFromBackend, connection: laneConnection, frameId: overlayFrameId, frameSize: effectiveFrameSize, vehicleState });
      const overlayVehicleData = selectVehicleData({ backendData: vehicleDataFromBackend, connection: vehicleConnection, frameId: overlayFrameId });
      const overlayPedestrianData = selectPedestrianData({ backendData: pedestrianDataFromBackend, connection: pedestrianConnection, frameId: overlayFrameId });
      const overlayTrafficSigns = selectTrafficSigns({ backendData: trafficSignsFromBackend, connection: trafficSignConnection, frameId: overlayFrameId, frameSize: effectiveFrameSize });

      // Only render real detection layers when connected to backend
      // In demo mode, SceneLayer handles all rendering (including road markings)
      return (
        <Suspense fallback={null}>
          {/* Lane Layer - only when connected to backend */}
          {isRealMode && (
            <LaneLayer laneData={overlayLaneData} currentFrameId={overlayFrameId} viewport={viewport} frameSize={effectiveFrameSize} />
          )}

          {/* Real Detection Layers - only when connected to backend */}
          {isRealMode && overlayVehicleData && (
            <VehicleLayer detections={overlayVehicleData} currentFrameId={overlayFrameId} viewport={viewport} frameSize={effectiveFrameSize} />
          )}
          {isRealMode && overlayPedestrianData && (
            <PedestrianLayer detections={overlayPedestrianData} currentFrameId={overlayFrameId} viewport={viewport} frameSize={effectiveFrameSize} />
          )}
          {isRealMode && overlayTrafficSigns.length > 0 && (
            <TrafficSignLayer signs={overlayTrafficSigns} currentFrameId={overlayFrameId} viewport={viewport} frameSize={effectiveFrameSize} />
          )}

          {/* Frame info badges */}
          <div className="frame-sync-badge"><span>{t('stat.frame')}</span><strong>{overlayFrameId ?? "--"}</strong></div>
          <div className="overlay-source-badge"><span>{isRealMode ? t('live.realtime') : t('live.demo')}</span></div>
        </Suspense>
      );
    },
    [frameSize, laneConnection, laneDataFromBackend, vehicleConnection, vehicleDataFromBackend, pedestrianConnection, pedestrianDataFromBackend, trafficSignConnection, trafficSignsFromBackend, t],
  );

  return (
    <main className={`dashboard-shell dashboard-shell--${assistState.tone}`}>
      <header className="dashboard-header">
        <div className="header-left"><h1 className="dashboard-title">ADAS Dashboard</h1></div>
        <div className="header-right">
          <ThemeToggle isDark={isDark} toggleTheme={toggleTheme} t={t} />
          <LanguageSelector language={language} setLanguage={setLanguage} t={t} />
        </div>
      </header>

      <section className="driver-topbar" aria-label={t('assist.attending')}>
        <div className="driver-topbar__main">
          <span className="driver-topbar__label">{t('assist.attending')}</span>
          <strong>{assistState.title}</strong>
          <p>{assistState.message}</p>
        </div>
        <div className="driver-readouts" aria-label={t('assist.monitoring')}>
          <div><span>{t('stat.lane')}</span><strong>{readableLaneStatus(laneData?.lane_status || warningData?.lane_status || "WAITING", t)}</strong></div>
          <div><span>{t('stat.sign')}</span><strong>{readableSignStatus(trafficSigns?.[0]?.class_name || warningData?.traffic_sign_status || "Scanning", t)}</strong></div>
          <div><span>{t('stat.pedestrian')}</span><strong>{(pedestrianData?.count || vehicleData?.count > 0 ? pedestrianData?.count : 0) || 0}</strong></div>
          <div><span>{t('stat.vehicle')}</span><strong>{vehicleData?.count || 0}</strong></div>
          <div><span>{t('stat.source')}</span><strong>{isConnected(cameraConnection) ? t('live.realtime') : t('live.demo')}</strong></div>
          <div className="vehicle-control-info">
            <span>Tốc độ</span><strong>{Math.round(vehicleState.speed)} km/h</strong>
            <span className="control-hint">← → để di chuyển</span>
          </div>
        </div>
      </section>

      <div className="dashboard-grid">
        <section className="dashboard-primary" aria-label={t('nav.dashboard')}>
          <CameraView overlayRenderer={renderOverlays} onFrameChange={handleFrameChange} onConnectionChange={setCameraConnection} vehicleState={vehicleState} />
          <div className="stream-strip" aria-label="Trạng thái luồng dữ liệu">
            <ChannelStatus label={t('stat.lane')} connection={laneConnection} t={t} />
            <ChannelStatus label={t('stat.sign')} connection={trafficSignConnection} t={t} />
            <ChannelStatus label={t('stat.pedestrian')} connection={pedestrianConnection} t={t} />
            <ChannelStatus label={t('stat.vehicle')} connection={vehicleConnection} t={t} />
            <ChannelStatus label="Cảnh báo" connection={warningConnection} t={t} />
            <div className="channel-status"><span className="channel-status__dot" aria-hidden="true" /><span>{t('stat.frame')}</span><strong>{frameId ?? "--"}</strong></div>
          </div>
        </section>
        <WarningPanel warningData={warningData} />
      </div>
    </main>
  );
}
