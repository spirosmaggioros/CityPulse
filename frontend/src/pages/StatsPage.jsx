import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../api/axios";
import logo from "../assets/logo.webp";
import "./StatsPage.css";

const DEPT_COLORS = {
  POLICE: "#4a90d9",
  FIRE_DEPARTMENT: "#e94560",
  MUNICIPALITY: "#2ecc71",
};

const STATUS_COLORS = {
  OPEN: "#f59e0b",
  IN_PROGRESS: "#6c63ff",
  RESOLVED: "#10b981",
};

function FlagImg({ iso, size = 20 }) {
  if (!iso || iso === "-99") return null;
  let code = iso.toLowerCase();
  // Handle Taiwan special case
  if (code === "cn-tw") {
    code = "tw";
  }
  const isExtension = code.includes("-") || code.includes(".");
  const ext = isExtension ? ".svg" : ".png";
  return (
    <img
      src={`https://flagcdn.com/w40/${code}${ext}`}
      srcSet={`https://flagcdn.com/w80/${code}${ext} 2x`}
      width={size}
      alt={iso}
      className="country-flag"
      loading="lazy"
    />
  );
}

function BarChart({ data, colors, title }) {
  if (!data || Object.keys(data).length === 0) {
    return <p className="stat-empty">No data</p>;
  }
  const max = Math.max(...Object.values(data), 1);
  return (
    <div className="bar-chart">
      <h4 className="bar-chart-title">{title}</h4>
      {Object.entries(data).map(([key, val]) => (
        <div className="bar-row" key={key}>
          <span className="bar-label">{key.replace(/_/g, " ")}</span>
          <div className="bar-track">
            <div
              className="bar-fill"
              style={{
                width: `${(val / max) * 100}%`,
                background: colors?.[key] || "#6c63ff",
              }}
            />
          </div>
          <span className="bar-value">{fmtNum(val)}</span>
        </div>
      ))}
    </div>
  );
}

function fmtNum(n) {
  if (n == null) return "0";
  const v = Number(n);
  if (v >= 1_000_000_000) return `${(v / 1_000_000_000).toFixed(3)}b`;
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(3)}m`;
  if (v >= 100_000) return `${(v / 1_000).toFixed(1)}k`;
  return v.toLocaleString();
}

function StatCard({ label, value, icon }) {
  return (
    <div className="stat-card">
      <div className="stat-card-icon">{icon}</div>
      <div className="stat-card-body">
        <span className="stat-card-value">{fmtNum(value)}</span>
        <span className="stat-card-label">{label}</span>
      </div>
    </div>
  );
}

function timeAgo(dateStr) {
  if (!dateStr) return "";
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diffSec = Math.max(0, Math.floor((now - then) / 1000));
  if (diffSec < 60) return `${diffSec}s ago`;
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  if (diffDay < 30) return `${diffDay}d ago`;
  const diffMo = Math.floor(diffDay / 30);
  return `${diffMo}mo ago`;
}

export default function StatsPage() {
  const navigate = useNavigate();
  const [globalStats, setGlobalStats] = useState(null);
  const [topCountries, setTopCountries] = useState([]);
  const [selectedCountry, setSelectedCountry] = useState(null);
  const [countryStats, setCountryStats] = useState(null);
  const [liveFeed, setLiveFeed] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchAll() {
      try {
        const [gRes, tcRes, lfRes] = await Promise.all([
          API.get("/stats/global"),
          API.get("/stats/top-countries?limit=15"),
          API.get("/stats/live-feed?limit=20"),
        ]);
        setGlobalStats(gRes.data);
        setTopCountries(tcRes.data);
        setLiveFeed(lfRes.data);
      } catch (err) {
        console.error("Failed to fetch stats:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchAll();
  }, []);

  const fetchCountryStats = async (iso_a2) => {
    setSelectedCountry(iso_a2);
    try {
      const res = await API.get(`/stats/country/${iso_a2}`);
      setCountryStats(res.data);
    } catch (err) {
      console.error("Failed to fetch country stats:", err);
      setCountryStats(null);
    }
  };

  if (loading) {
    return (
      <div className="stats-page">
        <div className="stats-loading">Loading statistics...</div>
      </div>
    );
  }

  const maxCount = topCountries.length > 0 ? topCountries[0].count : 1;

  return (
    <div className="stats-page">
      {/* Header */}
      <header className="stats-header">
        <div className="stats-header-left" onClick={() => navigate("/")} style={{ cursor: "pointer" }}>
          <img src={logo} alt="Logo" className="stats-logo" />
          <h1>Statistics</h1>
        </div>
        <button className="stats-back-btn" onClick={() => navigate("/")}>
          ← Back to Home
        </button>
      </header>

      {/* Global overview cards */}
      <section className="stats-section">
        <h2 className="stats-section-title">Global Overview</h2>
        <div className="stat-cards-row">
          <StatCard
            label="Total Reports"
            value={globalStats?.total_reports}
            icon={
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#6c63ff" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            }
          />
          <StatCard
            label="Urgent"
            value={globalStats?.urgent_count}
            icon={
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#e94560" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            }
          />
          <StatCard
            label="Total Likes"
            value={globalStats?.total_likes}
            icon={
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>
            }
          />
          <StatCard
            label="Total Dislikes"
            value={globalStats?.total_dislikes}
            icon={
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2"><path d="M10 15V19a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/></svg>
            }
          />
        </div>
      </section>

      {/* Charts row + Live Feed */}
      <section className="stats-section">
        <div className="stats-charts-row">
          <div className="stats-chart-card">
            <BarChart
              title="Reports by Department"
              data={globalStats?.by_department}
              colors={DEPT_COLORS}
            />
          </div>
          <div className="stats-chart-card">
            <BarChart
              title="Reports by Status"
              data={globalStats?.by_status}
              colors={STATUS_COLORS}
            />
          </div>
          <div className="live-feed-card">
            <h4>Live Feed</h4>
            <div className="live-feed-list">
              {liveFeed.length === 0 && (
                <p className="stat-empty">No active reports.</p>
              )}
              {liveFeed.map((r) => (
                <div className="live-feed-item" key={r.id}>
                  <div
                    className={`live-feed-dot${r.urgent ? " urgent" : ""}`}
                    style={{ background: DEPT_COLORS[r.department] || "#888" }}
                  />
                  <div className="live-feed-body">
                    <div className="live-feed-title">{r.title}</div>
                    <div className="live-feed-meta">
                      <span className="live-feed-dept">
                        {r.department?.replace(/_/g, " ")}
                      </span>
                      <span>·</span>
                      <span>{r.status?.replace(/_/g, " ")}</span>
                      {r.country_code && (
                        <>
                          <span>·</span>
                          <FlagImg iso={r.country_code} size={14} />
                        </>
                      )}
                    </div>
                  </div>
                  <span className="live-feed-time">{timeAgo(r.created_at)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Top countries ranking */}
      <section className="stats-section">
        <h2 className="stats-section-title">Top Countries by Reports</h2>
        <div className="top-countries-grid">
          <div className="top-countries-list">
            {topCountries.map((c, idx) => (
              <div
                key={c.iso_a2 || idx}
                className={`top-country-row ${selectedCountry === c.iso_a2 ? "active" : ""}`}
                onClick={() => fetchCountryStats(c.iso_a2)}
              >
                <span className="top-country-rank">#{idx + 1}</span>
                <FlagImg iso={c.iso_a2} size={24} />
                <span className="top-country-name">{c.country}</span>
                <div className="top-country-bar-track">
                  <div
                    className="top-country-bar-fill"
                    style={{ width: `${(c.count / maxCount) * 100}%` }}
                  />
                </div>
                <span className="top-country-count">{fmtNum(c.count)}</span>
              </div>
            ))}
            {topCountries.length === 0 && (
              <p className="stat-empty">No country data available.</p>
            )}
          </div>

          {/* Country detail panel */}
          <div className="country-detail-panel">
            {countryStats ? (
              <>
                <div className="country-detail-header">
                  <FlagImg iso={countryStats.iso_a2} size={32} />
                  <h3>{countryStats.country}</h3>
                </div>
                <div className="stat-cards-row compact">
                  <StatCard label="Reports" value={countryStats.total_reports} icon={
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6c63ff" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                  } />
                  <StatCard label="Urgent" value={countryStats.urgent_count} icon={
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#e94560" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                  } />
                  <StatCard label="Likes" value={countryStats.total_likes} icon={
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>
                  } />
                </div>
                <BarChart
                  title="By Department"
                  data={countryStats.by_department}
                  colors={DEPT_COLORS}
                />
                <BarChart
                  title="By Status"
                  data={countryStats.by_status}
                  colors={STATUS_COLORS}
                />
              </>
            ) : (
              <div className="country-detail-empty">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#555" strokeWidth="1.5">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="2" y1="12" x2="22" y2="12" />
                  <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                </svg>
                <p>Select a country to view details</p>
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
