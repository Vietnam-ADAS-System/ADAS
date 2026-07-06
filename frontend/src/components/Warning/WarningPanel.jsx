import { useEffect, useMemo, useState } from "react";
import LaneWarningCard from "./LaneWarningCard.jsx";
import SystemStatusCard from "./SystemStatusCard.jsx";
import TrafficSignWarningCard from "./TrafficSignWarningCard.jsx";
import WarningBanner from "./WarningBanner.jsx";
import WarningHistory from "./WarningHistory.jsx";
import "./warning.style.css";

function shouldStoreWarning(warningData, previous) {
  if (!warningData?.active) {
    return false;
  }

  const latest = previous[0];
  return (
    !latest ||
    latest.warning_type !== warningData.warning_type ||
    latest.warning_message !== warningData.warning_message ||
    Math.abs(Number(latest.frame_id) - Number(warningData.frame_id)) > 45
  );
}

export default function WarningPanel({ warningData }) {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    setHistory((previous) => {
      if (!shouldStoreWarning(warningData, previous)) {
        return previous;
      }

      return [warningData, ...previous].slice(0, 6);
    });
  }, [warningData]);

  const systemStatus = useMemo(() => warningData?.system_status || {}, [warningData]);

  return (
    <aside className="warning-panel" aria-label="ADAS warning panel">
      <WarningBanner warningData={warningData} />
      <LaneWarningCard warningData={warningData} />
      <TrafficSignWarningCard warningData={warningData} />
      <SystemStatusCard status={systemStatus} />
      <WarningHistory history={history} />
    </aside>
  );
}
