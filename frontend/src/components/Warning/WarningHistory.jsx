function formatTime(timestamp) {
  const date = timestamp ? new Date(timestamp) : new Date();

  if (Number.isNaN(date.getTime())) {
    return "--:--:--";
  }

  return date.toLocaleTimeString("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export default function WarningHistory({ history }) {
  return (
    <section className="warning-section warning-history">
      <div className="section-title">Lịch sử cảnh báo</div>
      {history.length === 0 ? (
        <p>Chưa có cảnh báo</p>
      ) : (
        <div className="warning-history-list">
          {history.map((item) => (
            <div className="warning-history-row" key={`${item.timestamp}-${item.warning_type}-${item.frame_id}`}>
              <span>{formatTime(item.timestamp)}</span>
              <strong>{item.warning_message}</strong>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
