import "./ReportCard.css";

const DEPT_LABELS = {
  POLICE: "Police",
  FIRE_DEPARTMENT: "Fire Dept",
  MUNICIPALITY: "Municipality",
};

const STATUS_LABELS = {
  OPEN: "Open",
  IN_PROGRESS: "In Progress",
  RESOLVED: "Resolved",
};

export default function ReportCard({ report }) {
  const {
    title,
    description,
    department,
    location,
    image_url,
    status,
    urgent,
  } = report;

  return (
    <div className={`report-card ${urgent ? "urgent" : ""}`}>
      {image_url && (
        <div className="report-image">
          <img src={image_url} alt={title} loading="lazy" />
        </div>
      )}

      <div className="report-body">
        <div className="report-top-row">
          <span className={`dept-badge dept-${department.toLowerCase()}`}>
            {DEPT_LABELS[department] || department}
          </span>
          <span className={`status-badge status-${status.toLowerCase()}`}>
            {STATUS_LABELS[status] || status}
          </span>
        </div>

        <h3 className="report-title">{title}</h3>
        <p className="report-description">{description}</p>

        <div className="report-meta">
          <span className="report-location">📍 {location}</span>
          {urgent && (
            <span className="urgent-badge">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
              Urgent
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
