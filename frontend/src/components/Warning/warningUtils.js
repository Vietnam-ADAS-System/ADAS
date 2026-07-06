export function priorityClass(level = "INFO") {
  const normalized = String(level).toLowerCase();

  if (normalized === "critical") {
    return "critical";
  }

  if (normalized === "high") {
    return "high";
  }

  if (normalized === "medium") {
    return "medium";
  }

  if (normalized === "low") {
    return "low";
  }

  return "info";
}

export function laneStatusClass(status = "") {
  if (status === "LANE_DEPARTURE") {
    return "departure";
  }

  if (status === "NEAR_BOUNDARY") {
    return "near";
  }

  return status === "SAFE" ? "safe" : "info";
}

export function moduleStatusClass(status = "") {
  const normalized = String(status).toUpperCase();

  if (
    normalized === "RUNNING" ||
    normalized === "ONLINE" ||
    normalized === "CONNECTED" ||
    normalized === "SAFE"
  ) {
    return "running";
  }

  if (normalized === "IDLE" || normalized === "LOADING") {
    return "info";
  }

  if (normalized === "NEAR_BOUNDARY") {
    return "medium";
  }

  return "critical";
}

export function formatTimestamp(timestamp) {
  if (!timestamp) {
    return "--:--:--";
  }

  return new Intl.DateTimeFormat("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false
  }).format(new Date(timestamp));
}
