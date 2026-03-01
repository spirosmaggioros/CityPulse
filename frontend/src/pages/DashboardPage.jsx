import { useEffect, useRef, useState, useCallback } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { useNavigate } from "react-router-dom";
import API from "../api/axios";
import ReportCard from "../components/ReportCard";
import ReportDetailPopup from "../components/ReportDetailPopup";
import logo from "../assets/logo.webp";
import "./Dashboard.css";

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || "";
const DEFAULT_RADIUS = 10000;
const REFETCH_THRESHOLD_KM = DEFAULT_RADIUS / 1000 * 0.5; // 5 km
/* ── HTML escape helper to prevent XSS ── */
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}// const DEFAULT_LIMIT = -1;

const MAP_STATE_KEY = "dashboard_map_state";

const COUNTRY_RECHECK_THRESHOLD_KM = 30;
const COUNTRY_MIN_ZOOM = 3;
const COUNTRY_MAX_ZOOM = 7;

/** Below this zoom level we skip closest-reports fetches (too zoomed out). */
const REPORTS_MIN_ZOOM = 10;

const DEPT_COLORS = {
  POLICE: "#4a90d9",
  FIRE_DEPARTMENT: "#e94560",
  MUNICIPALITY: "#2ecc71",
};

function haversineKm(lat1, lng1, lat2, lng2) {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function reportsToGeoJSON(reports) {
  return {
    type: "FeatureCollection",
    features: reports
      .filter((r) => r.coordinates?.coordinates)
      .map((r) => ({
        type: "Feature",
        properties: {
          id: r.id,
          title: r.title,
          location: r.location,
          department: r.department,
          color: DEPT_COLORS[r.department] || "#888",
        },
        geometry: {
          type: "Point",
          coordinates: r.coordinates.coordinates,
        },
      })),
  };
}

/* ---- Client-side ray-casting point-in-polygon ---- */
function pointInRing(lng, lat, ring) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const xi = ring[i][0], yi = ring[i][1];
    const xj = ring[j][0], yj = ring[j][1];
    if ((yi > lat) !== (yj > lat) && lng < ((xj - xi) * (lat - yi)) / (yj - yi) + xi) {
      inside = !inside;
    }
  }
  return inside;
}

function pointInPolygon(lng, lat, polygon) {
  // polygon.coordinates: [outerRing, ...holes]
  if (!pointInRing(lng, lat, polygon.coordinates[0])) return false;
  // Check holes
  for (let i = 1; i < polygon.coordinates.length; i++) {
    if (pointInRing(lng, lat, polygon.coordinates[i])) return false;
  }
  return true;
}

function pointInMultiPolygon(lng, lat, geometry) {
  if (!geometry) return false;
  if (geometry.type === "Polygon") {
    return pointInPolygon(lng, lat, geometry);
  }
  if (geometry.type === "MultiPolygon") {
    for (const polyCoords of geometry.coordinates) {
      const poly = { type: "Polygon", coordinates: polyCoords };
      if (pointInPolygon(lng, lat, poly)) return true;
    }
  }
  return false;
}

export default function DashboardPage() {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const mapReady = useRef(false);        // true once source + layers exist
  const lastFetchCenter = useRef(null);
  const navigate = useNavigate();
  const [reports, setReports] = useState([]);
  const reportsRef = useRef([]);          // always mirrors `reports` state
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedReport, setSelectedReport] = useState(null);
  const [filters, setFilters] = useState({
    department: "",
    status: "unresolved",
    urgent: "",
  });
  const hoverPopup = useRef(null);

  /* ---------- Country state ---------- */
  const [countryName, setCountryName] = useState(null);
  const cachedCountry = useRef(null); // { name, iso_a2, iso_a3, geometry }
  const lastCountryCheckCenter = useRef(null);

  /* ---------- Debounce timers ---------- */
  const fetchDebounceTimer = useRef(null);
  const countryDebounceTimer = useRef(null);

  /* ---------- Stable-ref for callbacks used in event listeners ---------- */
  const fetchReportsRef = useRef(null);
  const checkCountryRef = useRef(null);

  /* ---------- Fetch closest reports ---------- */
  const fetchReports = useCallback(
    async (lng, lat, filtersOverride) => {
      const f = filtersOverride || filters;
      try {
        const params = {
          lng,
          lat,
          radius_meters: DEFAULT_RADIUS,
        };
        if (f.department) params.department = f.department;
        if (f.status && f.status !== "unresolved") params.status = f.status;
        if (f.status === "unresolved") params.status = "unresolved";
        if (f.urgent !== "") params.urgent = f.urgent === "true";

        const res = await API.get("/reports/closest/", { params });
        setReports(res.data);
        lastFetchCenter.current = { lng, lat };
      } catch (err) {
        console.error("Failed to fetch reports:", err);
      }
    },
    [filters]
  );

  // Keep refs in sync with latest callback versions
  useEffect(() => { fetchReportsRef.current = fetchReports; }, [fetchReports]);

  /* ---------- Country detection ---------- */
  const checkCountry = useCallback(async (lng, lat, zoom) => {
    // Only check at appropriate zoom levels
    // if (zoom < COUNTRY_MIN_ZOOM || zoom > COUNTRY_MAX_ZOOM) {
    if (zoom < COUNTRY_MIN_ZOOM) {
      setCountryName(null);
      cachedCountry.current = null;
      lastCountryCheckCenter.current = null;
      return;
    };

    // If we have a cached polygon, do client-side point-in-polygon first
    if (cachedCountry.current && cachedCountry.current.geometry) {
      if (pointInMultiPolygon(lng, lat, cachedCountry.current.geometry)) {
        // Still in the same country — check if we moved far enough to warrant a re-check
        if (lastCountryCheckCenter.current) {
          const dist = haversineKm(
            lastCountryCheckCenter.current.lat,
            lastCountryCheckCenter.current.lng,
            lat,
            lng
          );
          if (dist < COUNTRY_RECHECK_THRESHOLD_KM) return;
        }
        // Update last check position but keep the country
        lastCountryCheckCenter.current = { lng, lat };
        return;
      }
    }

    // Outside cached polygon or no cached polygon — check threshold
    if (lastCountryCheckCenter.current) {
      const dist = haversineKm(
        lastCountryCheckCenter.current.lat,
        lastCountryCheckCenter.current.lng,
        lat,
        lng
      );
      if (dist < COUNTRY_RECHECK_THRESHOLD_KM && cachedCountry.current) return;
    }

    // Fetch from backend
    try {
      const res = await API.get("/geo/country", { params: { lng, lat } });
      lastCountryCheckCenter.current = { lng, lat };
      if (res.data.country) {
        cachedCountry.current = res.data.country;
        setCountryName(res.data.country.name);
      } else {
        cachedCountry.current = null;
        setCountryName(null);
      }
    } catch (err) {
      console.error("Failed to fetch country:", err);
    }
  }, []);

  useEffect(() => { checkCountryRef.current = checkCountry; }, [checkCountry]);

  /* ---------- Mapbox init ---------- */
  useEffect(() => {
    if (map.current || !mapContainer.current) return;
    mapReady.current = false;

    mapboxgl.accessToken = MAPBOX_TOKEN;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/dark-v11",
      center: (() => {
        try {
          const s = JSON.parse(sessionStorage.getItem(MAP_STATE_KEY));
          if (s?.center) return s.center;
        } catch {}
        return [23.7275, 37.9838];
      })(),
      zoom: (() => {
        try {
          const s = JSON.parse(sessionStorage.getItem(MAP_STATE_KEY));
          if (s?.zoom != null) return s.zoom;
        } catch {}
        return 12;
      })(),
    });

    map.current.addControl(new mapboxgl.NavigationControl(), "top-right");

    map.current.on("load", () => {
      /* -- Cluster source -- */
      map.current.addSource("reports", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
        cluster: true,
        clusterMaxZoom: 14,
        clusterRadius: 50,
      });

      /* -- Cluster circles -- */
      map.current.addLayer({
        id: "clusters",
        type: "circle",
        source: "reports",
        filter: ["has", "point_count"],
        paint: {
          "circle-color": [
            "step",
            ["get", "point_count"],
            "#6c63ff",
            10,
            "#4f46e5",
            30,
            "#3730a3",
          ],
          "circle-radius": [
            "step",
            ["get", "point_count"],
            18,
            10,
            24,
            30,
            30,
          ],
          "circle-stroke-width": 2,
          "circle-stroke-color": "rgba(255,255,255,0.25)",
        },
      });

      /* -- Cluster count labels -- */
      map.current.addLayer({
        id: "cluster-count",
        type: "symbol",
        source: "reports",
        filter: ["has", "point_count"],
        layout: {
          "text-field": "{point_count_abbreviated}",
          "text-font": ["DIN Pro Medium", "Arial Unicode MS Bold"],
          "text-size": 13,
        },
        paint: {
          "text-color": "#ffffff",
        },
      });

      /* -- Unclustered points -- */
      map.current.addLayer({
        id: "unclustered-point",
        type: "circle",
        source: "reports",
        filter: ["!", ["has", "point_count"]],
        paint: {
          "circle-color": ["get", "color"],
          "circle-radius": 7,
          "circle-stroke-width": 2,
          "circle-stroke-color": "#ffffff",
        },
      });

      /* -- Click cluster to zoom -- */
      map.current.on("click", "clusters", (e) => {
        const features = map.current.queryRenderedFeatures(e.point, {
          layers: ["clusters"],
        });
        const clusterId = features[0].properties.cluster_id;
        map.current
          .getSource("reports")
          .getClusterExpansionZoom(clusterId, (err, zoom) => {
            if (err) return;
            map.current.easeTo({
              center: features[0].geometry.coordinates,
              zoom,
            });
          });
      });

      /* -- Click unclustered point -> show detail -- */
      map.current.on("click", "unclustered-point", (e) => {
        const props = e.features[0].properties;
        const reportId = props.id;
        setReports((prev) => {
          const found = prev.find((r) => r.id === reportId);
          if (found) setSelectedReport(found);
          return prev;
        });
      });

      /* -- Hover popup on unclustered point -- */
      map.current.on("mouseenter", "unclustered-point", (e) => {
        map.current.getCanvas().style.cursor = "pointer";
        const coords = e.features[0].geometry.coordinates.slice();
        const props = e.features[0].properties;
        const deptClass = props.department.toLowerCase();
        const html = `<div class="popup-inner">
          <strong>${escapeHtml(props.title)}</strong>
          <p>${escapeHtml(props.location)}</p>
          <span class="popup-dept popup-dept-${deptClass}">${props.department.replace("_", " ")}</span>
        </div>`;

        if (hoverPopup.current) hoverPopup.current.remove();
        hoverPopup.current = new mapboxgl.Popup({
          offset: 15,
          closeButton: false,
          closeOnClick: false,
        })
          .setLngLat(coords)
          .setHTML(html)
          .addTo(map.current);
      });

      map.current.on("mouseleave", "unclustered-point", () => {
        map.current.getCanvas().style.cursor = "";
        if (hoverPopup.current) {
          hoverPopup.current.remove();
          hoverPopup.current = null;
        }
      });

      /* -- Cursor for cluster -- */
      map.current.on("mouseenter", "clusters", () => {
        map.current.getCanvas().style.cursor = "pointer";
      });
      map.current.on("mouseleave", "clusters", () => {
        map.current.getCanvas().style.cursor = "";
      });

      /* -- Mark source ready -- */
      mapReady.current = true;

      /* -- Apply any reports that arrived before the source was ready -- */
      if (reportsRef.current.length > 0) {
        const src = map.current.getSource("reports");
        if (src) src.setData(reportsToGeoJSON(reportsRef.current));
      }

      /* -- Initial fetch -- */
      const center = map.current.getCenter();
      const initialZoom = map.current.getZoom();
      if (initialZoom >= REPORTS_MIN_ZOOM) {
        fetchReportsRef.current(center.lng, center.lat);
      }
      checkCountryRef.current(center.lng, center.lat, initialZoom);
    });

    map.current.on("moveend", () => {
      const center = map.current.getCenter();
      const zoom = map.current.getZoom();

      // Persist map state so it survives navigation
      sessionStorage.setItem(
        MAP_STATE_KEY,
        JSON.stringify({ center: [center.lng, center.lat], zoom })
      );

      // Debounced report fetch (use ref to avoid stale closure)
      if (fetchDebounceTimer.current) clearTimeout(fetchDebounceTimer.current);
      fetchDebounceTimer.current = setTimeout(() => {
        // Skip closest queries when zoomed out too far
        if (zoom < REPORTS_MIN_ZOOM) {
          setReports([]);
          lastFetchCenter.current = null;
          return;
        }
        if (lastFetchCenter.current) {
          const dist = haversineKm(
            lastFetchCenter.current.lat,
            lastFetchCenter.current.lng,
            center.lat,
            center.lng
          );
          if (dist > REFETCH_THRESHOLD_KM) {
            fetchReportsRef.current(center.lng, center.lat);
          }
        } else {
          // First fetch after zoom-in from a zoomed-out state
          fetchReportsRef.current(center.lng, center.lat);
        }
      }, 300);

      // Debounced country check (use ref to avoid stale closure)
      if (countryDebounceTimer.current) clearTimeout(countryDebounceTimer.current);
      countryDebounceTimer.current = setTimeout(() => {
        checkCountryRef.current(center.lng, center.lat, zoom);
      }, 400);
    });

    return () => {
      if (fetchDebounceTimer.current) clearTimeout(fetchDebounceTimer.current);
      if (countryDebounceTimer.current) clearTimeout(countryDebounceTimer.current);
      mapReady.current = false;
      map.current?.remove();
      map.current = null;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /* ---------- Re-fetch when filters change ---------- */
  useEffect(() => {
    if (!map.current || !lastFetchCenter.current) return;
    const { lng, lat } = lastFetchCenter.current;
    fetchReports(lng, lat, filters);
  }, [filters]); // eslint-disable-line react-hooks/exhaustive-deps

  /* ---------- Resize map when sidebar toggles ---------- */
  useEffect(() => {
    if (!map.current) return;
    const timer = setTimeout(() => map.current.resize(), 300);
    return () => clearTimeout(timer);
  }, [sidebarOpen]);

  /* ---------- Update GeoJSON source when reports change ---------- */
  useEffect(() => {
    reportsRef.current = reports;          // keep ref in sync
    if (!map.current || !mapReady.current) return;
    const src = map.current.getSource("reports");
    if (src) {
      src.setData(reportsToGeoJSON(reports));
    }
  }, [reports]);

  /* ---------- Hover handlers for sidebar cards ---------- */
  const handleReportHover = useCallback((report) => {
    if (!map.current || !report.coordinates?.coordinates) return;
    const [lng, lat] = report.coordinates.coordinates;
    const deptClass = report.department.toLowerCase();

    if (hoverPopup.current) hoverPopup.current.remove();
    hoverPopup.current = new mapboxgl.Popup({
      offset: 15,
      closeButton: false,
      closeOnClick: false,
    })
      .setLngLat([lng, lat])
      .setHTML(
        `<div class="popup-inner">
          <strong>${escapeHtml(report.title)}</strong>
          <p>${escapeHtml(report.location)}</p>
          <span class="popup-dept popup-dept-${deptClass}">${report.department.replace("_", " ")}</span>
        </div>`
      )
      .addTo(map.current);
  }, []);

  const handleReportLeave = useCallback(() => {
    if (hoverPopup.current) {
      hoverPopup.current.remove();
      hoverPopup.current = null;
    }
  }, []);

  /* ---------- Filter change handler ---------- */
  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters((prev) => ({ ...prev, [name]: value }));
  };

  /* ---------- Report CRUD callbacks ---------- */
  const handleReportUpdated = (updatedReport) => {
    setReports((prev) =>
      prev.map((r) => (r.id === updatedReport.id ? updatedReport : r))
    );
    setSelectedReport(updatedReport);
  };

  const handleReportDeleted = (reportId) => {
    setReports((prev) => prev.filter((r) => r.id !== reportId));
    setSelectedReport(null);
  };

  return (
    <div className="dashboard">
      {/* ---------- Sidebar ---------- */}
      <aside className={`sidebar ${sidebarOpen ? "open" : "collapsed"}`}>
        <div className="sidebar-header">
          <div className="sidebar-brand" onClick={() => navigate("/")} style={{ cursor: "pointer" }}>
            <img src={logo} alt="Logo" className="sidebar-logo" />
            {sidebarOpen && <h2>Reports</h2>}
          </div>
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            title={sidebarOpen ? "Collapse" : "Expand"}
          >
            {sidebarOpen ? "◀" : "▶"}
          </button>
        </div>

        {sidebarOpen && (
          <>
            <div className="sidebar-filters">
              <div className="filter-group">
                <label>Department</label>
                <select
                  name="department"
                  value={filters.department}
                  onChange={handleFilterChange}
                >
                  <option value="">All</option>
                  <option value="POLICE">Police</option>
                  <option value="FIRE_DEPARTMENT">Fire Department</option>
                  <option value="MUNICIPALITY">Municipality</option>
                </select>
              </div>
              <div className="filter-group">
                <label>Status</label>
                <select
                  name="status"
                  value={filters.status}
                  onChange={handleFilterChange}
                >
                  <option value="unresolved">Unresolved</option>
                  <option value="">All</option>
                  <option value="OPEN">Open</option>
                  <option value="IN_PROGRESS">In Progress</option>
                  <option value="RESOLVED">Resolved</option>
                </select>
              </div>
              <div className="filter-group">
                <label>Urgency</label>
                <select
                  name="urgent"
                  value={filters.urgent}
                  onChange={handleFilterChange}
                >
                  <option value="">All</option>
                  <option value="true">Urgent only</option>
                  <option value="false">Non-urgent only</option>
                </select>
              </div>
            </div>

            <div className="sidebar-reports">
              {reports.length === 0 && (
                <p className="no-reports">No reports found.</p>
              )}
              {reports.map((report) => (
                <div
                  key={report.id}
                  onMouseEnter={() => handleReportHover(report)}
                  onMouseLeave={handleReportLeave}
                  onClick={() => setSelectedReport(report)}
                >
                  <ReportCard report={report} />
                </div>
              ))}
            </div>
          </>
        )}
      </aside>

      {/* ---------- Map ---------- */}
      <div className="map-wrapper" ref={mapContainer} />

      {/* ---------- Country badge ---------- */}
      {countryName && (
        <div className="country-badge">
          {cachedCountry.current?.iso_a2 && cachedCountry.current.iso_a2 !== "-99" && (
            <>
              {(() => {
                let code = cachedCountry.current.iso_a2.toLowerCase();
                if (code === "cn-tw") code = "tw";
                const isExtension = code.includes("-") || code.includes(".");
                const ext = isExtension ? ".svg" : ".png";
                return (
                  <img
                    src={`https://flagcdn.com/w40/${code}${ext}`}
                    srcSet={`https://flagcdn.com/w80/${code}${ext} 2x`}
                    width="20"
                    alt={cachedCountry.current.iso_a2}
                    className="country-badge-flag"
                  />
                );
              })()}
            </>
          )}
          {countryName}
        </div>
      )}

      {/* ---------- Report detail popup ---------- */}
      {selectedReport && (
        <ReportDetailPopup
          report={selectedReport}
          onClose={() => setSelectedReport(null)}
          onUpdated={handleReportUpdated}
          onDeleted={handleReportDeleted}
        />
      )}

      {/* ---------- Bottom bar ---------- */}
      <div className="bottom-bar">
        <button
          className="bottom-bar-btn"
          onClick={() => navigate("/")}
          title="Back to home"
        >
          Home
        </button>
        <button
          className="bottom-bar-btn"
          onClick={() => { window.location.href = "/chat/"; }}
          title="Report an incident"
        >
          Report
        </button>
        <button
          className="bottom-bar-btn"
          onClick={() => navigate("/stats")}
          title="View statistics"
        >
          Statistics
        </button>
      </div>
    </div>
  );
}
