const LEVEL_LABEL = {
  INFO: "THÔNG TIN",
  LOW: "THẤP",
  MEDIUM: "TRUNG BÌNH",
  HIGH: "CAO",
  CRITICAL: "KHẨN CẤP",
};

export default function WarningPriority({ level }) {
  const normalizedLevel = level || "INFO";

  return (
    <span className={`warning-priority warning-priority--${normalizedLevel}`}>
      {LEVEL_LABEL[normalizedLevel] || normalizedLevel}
    </span>
  );
}
