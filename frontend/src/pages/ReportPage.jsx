import { useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../api/axios";
import logo from "../assets/logo.webp";
import "./ReportForm.css";

const DEPARTMENTS = [
  { value: "POLICE", label: "Police" },
  { value: "FIRE_DEPARTMENT", label: "Fire Department" },
  { value: "MUNICIPALITY", label: "Municipality" },
];

export default function ReportPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    title: "",
    description: "",
    department: "MUNICIPALITY",
    location: "",
    image_url: "",
    urgent: false,
    longitude: "",
    latitude: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    const lng = parseFloat(form.longitude);
    const lat = parseFloat(form.latitude);

    if (isNaN(lng) || isNaN(lat)) {
      setError("Please enter valid coordinates");
      return;
    }

    setLoading(true);
    try {
      const payload = {
        title: form.title,
        description: form.description,
        department: form.department,
        location: form.location,
        urgent: form.urgent,
        image_url: form.image_url || null,
        coordinates: {
          type: "Point",
          coordinates: [lng, lat],
        },
      };

      await API.post("/reports", payload);
      navigate("/dashboard");
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === "string") {
        setError(detail);
      } else if (Array.isArray(detail)) {
        setError(detail.map((d) => d.msg).join(", "));
      } else {
        setError("Failed to create report");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="report-form-container">
      <div className="report-form-card">
        <div className="report-form-header">
          <img src={logo} alt="Logo" className="report-form-logo" />
          <h1>Submit a Report</h1>
          <p className="report-form-subtitle">Help your community</p>
        </div>

        {error && <div className="report-form-error">{error}</div>}

        <form onSubmit={handleSubmit} className="report-form">
          <div className="form-group">
            <label htmlFor="title">Title</label>
            <input
              id="title"
              name="title"
              type="text"
              value={form.title}
              onChange={handleChange}
              placeholder="Brief title for the report"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              name="description"
              value={form.description}
              onChange={handleChange}
              placeholder="Describe the issue in detail…"
              rows={4}
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="department">Department</label>
              <select
                id="department"
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

            <div className="form-group">
              <label htmlFor="location">Location</label>
              <input
                id="location"
                name="location"
                type="text"
                value={form.location}
                onChange={handleChange}
                placeholder="e.g. Syntagma Square"
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="longitude">Longitude</label>
              <input
                id="longitude"
                name="longitude"
                type="number"
                step="any"
                value={form.longitude}
                onChange={handleChange}
                placeholder="e.g. 23.7275"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="latitude">Latitude</label>
              <input
                id="latitude"
                name="latitude"
                type="number"
                step="any"
                value={form.latitude}
                onChange={handleChange}
                placeholder="e.g. 37.9838"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="image_url">Image URL (optional)</label>
            <input
              id="image_url"
              name="image_url"
              type="url"
              value={form.image_url}
              onChange={handleChange}
              placeholder="https://…"
            />
          </div>

          <div className="form-group-inline">
            <input
              id="urgent"
              name="urgent"
              type="checkbox"
              checked={form.urgent}
              onChange={handleChange}
            />
            <label htmlFor="urgent">Mark as urgent</label>
          </div>

          <div className="report-form-actions">
            <button
              type="button"
              className="btn-secondary"
              onClick={() => navigate("/dashboard")}
            >
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? "Submitting…" : "Submit Report"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
