import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import API from "../api/axios";
import "./ReportDetailPopup.css";

const DEPARTMENTS = [
  { value: "POLICE", label: "Police" },
  { value: "FIRE_DEPARTMENT", label: "Fire Department" },
  { value: "MUNICIPALITY", label: "Municipality" },
];

const STATUSES = [
  { value: "OPEN", label: "Open" },
  { value: "IN_PROGRESS", label: "In Progress" },
  { value: "RESOLVED", label: "Resolved" },
];

const DEPT_LABELS = {
  POLICE: "Police",
  FIRE_DEPARTMENT: "Fire Department",
  MUNICIPALITY: "Municipality",
};

const STATUS_LABELS = {
  OPEN: "Open",
  IN_PROGRESS: "In Progress",
  RESOLVED: "Resolved",
};

/* ---------- localStorage vote helpers ---------- */
function getVoteKey(reportId) {
  return `vote_${reportId}`;
}

function getSavedVote(reportId) {
  return localStorage.getItem(getVoteKey(reportId)); // "upvote" | "downvote" | null
}

function saveVote(reportId, vote) {
  if (vote) {
    localStorage.setItem(getVoteKey(reportId), vote);
  } else {
    localStorage.removeItem(getVoteKey(reportId));
  }
}

export default function ReportDetailPopup({
  report,
  onClose,
  onUpdated,
  onDeleted,
}) {
  const { user } = useAuth();
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [currentReport, setCurrentReport] = useState(report);
  const [userVote, setUserVote] = useState(getSavedVote(report.id));
  const [form, setForm] = useState({
    department: report.department,
    location: report.location,
    urgent: report.urgent,
    status: report.status,
    longitude: report.coordinates?.coordinates?.[0] ?? "",
    latitude: report.coordinates?.coordinates?.[1] ?? "",
  });

  useEffect(() => {
    setCurrentReport(report);
    setUserVote(getSavedVote(report.id));
  }, [report]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  /* ---------- Voting ---------- */
  const handleVote = async (voteType) => {
    try {
      if (userVote === voteType) {
        // Undo vote
        const res = await API.post(
          `/reports/${currentReport.id}/unvote?vote=${voteType}`
        );
        setCurrentReport(res.data);
        onUpdated(res.data);
        setUserVote(null);
        saveVote(currentReport.id, null);
      } else {
        // If switching vote, undo old first
        if (userVote) {
          const undoRes = await API.post(
            `/reports/${currentReport.id}/unvote?vote=${userVote}`
          );
          setCurrentReport(undoRes.data);
        }
        const res = await API.post(
          `/reports/${currentReport.id}/vote?vote=${voteType}`
        );
        setCurrentReport(res.data);
        onUpdated(res.data);
        setUserVote(voteType);
        saveVote(currentReport.id, voteType);
      }
    } catch (err) {
      console.error("Vote failed:", err);
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const lng = parseFloat(form.longitude);
      const lat = parseFloat(form.latitude);
      if (isNaN(lng) || isNaN(lat)) {
        setError("Please enter valid coordinates");
        setLoading(false);
        return;
      }

      const payload = {
        department: form.department,
        location: form.location,
        urgent: form.urgent,
        status: form.status,
        coordinates: { type: "Point", coordinates: [lng, lat] },
      };

      const res = await API.put(`/reports/${currentReport.id}`, payload);
      setCurrentReport(res.data);
      onUpdated(res.data);
      setEditing(false);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === "string") {
        setError(detail);
      } else if (Array.isArray(detail)) {
        setError(detail.map((d) => d.msg).join(", "));
      } else {
        setError("Failed to update report");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm("Are you sure you want to delete this report?")) return;
    setLoading(true);
    try {
      await API.delete(`/reports/${currentReport.id}`);
      onDeleted(currentReport.id);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Failed to delete report");
      setLoading(false);
    }
  };

  const isLoggedIn = !!user;

  /* ---------- Edit mode ---------- */
  if (editing) {
    return (
      <div className="popup-overlay" onClick={onClose}>
        <div className="popup-modal" onClick={(e) => e.stopPropagation()}>
          <button className="popup-close" onClick={onClose}>
            ✕
          </button>
          <h2>Edit Report</h2>

          {error && <div className="popup-error">{error}</div>}

          <form onSubmit={handleUpdate} className="popup-form">
            <div className="popup-form-row">
              <div className="popup-form-group">
                <label>Department</label>
                <select
                  name="department"
                  value={form.department}
                  onChange={handleChange}
                >
                  {DEPARTMENTS.map((d) => (
                    <option key={d.value} value={d.value}>
                      {d.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="popup-form-group">
                <label>Status</label>
                <select
                  name="status"
                  value={form.status}
                  onChange={handleChange}
                >
                  {STATUSES.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="popup-form-group">
              <label>Location</label>
              <input
                name="location"
                value={form.location}
                onChange={handleChange}
                required
              />
            </div>

            <div className="popup-form-row">
              <div className="popup-form-group">
                <label>Longitude</label>
                <input
                  name="longitude"
                  type="number"
                  step="any"
                  value={form.longitude}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="popup-form-group">
                <label>Latitude</label>
                <input
                  name="latitude"
                  type="number"
                  step="any"
                  value={form.latitude}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            <div className="popup-form-inline">
              <input
                name="urgent"
                type="checkbox"
                checked={form.urgent}
                onChange={handleChange}
              />
              <label>Urgent</label>
            </div>

            <div className="popup-actions">
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setEditing(false)}
              >
                Cancel
              </button>
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? "Saving…" : "Save Changes"}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  /* ---------- View mode ---------- */
  return (
    <div className="popup-overlay" onClick={onClose}>
      <div className="popup-modal" onClick={(e) => e.stopPropagation()}>
        <button className="popup-close" onClick={onClose}>
          ✕
        </button>

        {currentReport.image_url && (
          <div className="popup-image">
            <img src={currentReport.image_url} alt={currentReport.title} />
          </div>
        )}

        <div className="popup-content">
          <div className="popup-badges">
            <span
              className={`dept-badge dept-${currentReport.department.toLowerCase()}`}
            >
              {DEPT_LABELS[currentReport.department]}
            </span>
            <span
              className={`status-badge status-${currentReport.status.toLowerCase()}`}
            >
              {STATUS_LABELS[currentReport.status]}
            </span>
            {currentReport.urgent && (
              <span className="urgent-badge-popup">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                Urgent
              </span>
            )}
          </div>

          <h2 className="popup-title">{currentReport.title}</h2>
          <p className="popup-description">{currentReport.description}</p>

          <div className="popup-detail-row">
            <span className="popup-label">Location:</span>
            <span>{currentReport.location}</span>
          </div>

          <div className="popup-detail-row">
            <span className="popup-label">Coordinates:</span>
            <span>
              {currentReport.coordinates?.coordinates?.[1]?.toFixed(5)},{" "}
              {currentReport.coordinates?.coordinates?.[0]?.toFixed(5)}
            </span>
          </div>

          {currentReport.distance != null && (
            <div className="popup-detail-row">
              <span className="popup-label">Distance:</span>
              <span>
                {currentReport.distance < 1000
                  ? `${Math.round(currentReport.distance)}m`
                  : `${(currentReport.distance / 1000).toFixed(1)}km`}
              </span>
            </div>
          )}

          <div className="popup-detail-row">
            <span className="popup-label">Created:</span>
            <span>{new Date(currentReport.created_at).toLocaleString()}</span>
          </div>

          <div className="popup-detail-row">
            <span className="popup-label">Modified:</span>
            <span>{new Date(currentReport.modified_at).toLocaleString()}</span>
          </div>

          {/* ---------- Voting ---------- */}
          <div className="popup-votes">
            <button
              className={`vote-btn upvote ${userVote === "upvote" ? "active" : ""}`}
              onClick={() => handleVote("upvote")}
              title="Upvote"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>
              <span>{currentReport.likes ?? 0}</span>
            </button>
            <button
              className={`vote-btn downvote ${userVote === "downvote" ? "active" : ""}`}
              onClick={() => handleVote("downvote")}
              title="Downvote"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3H10z"/><path d="M17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/></svg>
              <span>{currentReport.dislikes ?? 0}</span>
            </button>
          </div>

          {error && <div className="popup-error">{error}</div>}

          {isLoggedIn && (
            <div className="popup-actions">
              <button
                className="btn-primary"
                onClick={() => setEditing(true)}
              >
                Edit Report
              </button>
              <button
                className="btn-danger"
                onClick={handleDelete}
                disabled={loading}
              >
                {loading ? "Deleting…" : "Delete Report"}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
