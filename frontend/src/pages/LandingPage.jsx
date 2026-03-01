import { useRef, useMemo, useState, useEffect, Suspense } from "react";
import { useNavigate } from "react-router-dom";
import { Canvas, useFrame } from "@react-three/fiber";
import { Sphere, OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import API from "../api/axios";
import logo from "../assets/logo.webp";
import mistralLogo from "../assets/mistral_logo.svg";
// import awsLogo from "../assets/aws.svg";
import awsLogo from "../assets/aws.png";
import "./Landing.css";

/* ─── 3D Earth Globe ─────────────────────────────────────── */
function EarthGlobe() {
  const meshRef = useRef();
  const pointsRef = useRef();

  useFrame((_, delta) => {
    if (meshRef.current) meshRef.current.rotation.y += delta * 0.12;
    if (pointsRef.current) pointsRef.current.rotation.y += delta * 0.12;
  });

  /* Generate dots on sphere surface */
  const dotPositions = useMemo(() => {
    const positions = [];
    const radius = 2.02;
    const count = 3000;
    for (let i = 0; i < count; i++) {
      const phi = Math.acos(-1 + (2 * i) / count);
      const theta = Math.sqrt(count * Math.PI) * phi;
      positions.push(
        radius * Math.cos(theta) * Math.sin(phi),
        radius * Math.sin(theta) * Math.sin(phi),
        radius * Math.cos(phi)
      );
    }
    return new Float32Array(positions);
  }, []);

  /* Glow ring points */
  const ringPositions = useMemo(() => {
    const positions = [];
    const segments = 128;
    const radius = 2.35;
    for (let i = 0; i <= segments; i++) {
      const angle = (i / segments) * Math.PI * 2;
      positions.push(
        Math.cos(angle) * radius,
        0,
        Math.sin(angle) * radius
      );
    }
    return new Float32Array(positions);
  }, []);

  return (
    <group>
      {/* Main globe */}
      <Sphere ref={meshRef} args={[2, 64, 64]}>
        <meshStandardMaterial
          color="#0a1628"
          transparent
          opacity={0.85}
          roughness={0.7}
          metalness={0.3}
        />
      </Sphere>

      {/* Grid/wireframe overlay */}
      <Sphere args={[2.01, 32, 32]}>
        <meshBasicMaterial
          color="#1a3a5c"
          wireframe
          transparent
          opacity={0.15}
        />
      </Sphere>

      {/* Dot cloud on surface */}
      <points ref={pointsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={dotPositions.length / 3}
            array={dotPositions}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          color="#00d4ff"
          size={0.02}
          transparent
          opacity={0.6}
          sizeAttenuation
        />
      </points>

      {/* Equator ring */}
      <line>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={ringPositions.length / 3}
            array={ringPositions}
            itemSize={3}
          />
        </bufferGeometry>
        <lineBasicMaterial color="#00d4ff" transparent opacity={0.2} />
      </line>

      {/* Glow */}
      <Sphere args={[2.15, 64, 64]}>
        <meshBasicMaterial
          color="#00d4ff"
          transparent
          opacity={0.04}
          side={THREE.BackSide}
        />
      </Sphere>

      {/* Ambient & point lights */}
      <ambientLight intensity={0.3} />
      <pointLight position={[5, 3, 5]} intensity={1.5} color="#00d4ff" />
      <pointLight position={[-5, -2, -5]} intensity={0.5} color="#6c63ff" />
    </group>
  );
}

/* ─── Number abbreviation ──────────────────────────────────── */
function fmtBigNum(n) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M+';
  if (n >= 1_000) return (n / 1_000).toFixed(1).replace(/\.0$/, '') + 'K+';
  return String(Math.floor(n));
}

/* ─── Animated counter ─────────────────────────────────────── */
function useCountUp(target, duration = 2000) {
  const ref = useRef(null);
  const observer = useRef(null);
  const hasAnimated = useRef(false);
  const isVisible = useRef(false);
  const prevTarget = useRef(target);
  const targetRef = useRef(target);
  targetRef.current = target;

  const runAnimation = () => {
    if (!ref.current || targetRef.current === 0) return;
    hasAnimated.current = true;
    const t = targetRef.current;
    const start = performance.now();
    const decimalMatch = String(t).match(/\.(\d+)/);
    const decimals = decimalMatch ? decimalMatch[1].length : 0;
    const tick = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const value = eased * t;
      if (ref.current) {
        ref.current.textContent = decimals > 0 ? value.toFixed(decimals) : fmtBigNum(value);
      }
      if (progress < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  };

  // Re-run animation when target changes (e.g. data loaded after mount)
  if (target !== prevTarget.current) {
    prevTarget.current = target;
    hasAnimated.current = false; // allow one new animation for the fresh value
    // If already visible, trigger animation immediately
    if (isVisible.current) {
      runAnimation();
    }
  }

  const setRef = (el) => {
    ref.current = el;
    if (el && !observer.current) {
      observer.current = new IntersectionObserver(
        ([entry]) => {
          isVisible.current = entry.isIntersecting;
          if (entry.isIntersecting && !hasAnimated.current) {
            runAnimation();
          }
        },
        { threshold: 0.5 }
      );
      observer.current.observe(el);
    }
  };

  return setRef;
}

function StatCard({ value, suffix = "", label, color }) {
  const numericValue = parseFloat(value);
  const countRef = useCountUp(numericValue, 2000);

  return (
    <div className="landing-stat-card">
      <div className="stat-value">
        <span ref={countRef}>0</span>
        <span className="stat-suffix">{suffix}</span>
      </div>
      <div className="stat-label">{label}</div>
      <div className="stat-accent" style={{ background: color }} />
    </div>
  );
}

/* ─── Process step ─────────────────────────────────────────── */
function ProcessStep({ number, title, description, icon }) {
  return (
    <div className="process-step">
      <div className="process-icon-wrap">
        <div className="process-icon">{icon}</div>
        <div className="process-arrow">▶</div>
      </div>
      <div className="process-text">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  );
}

/* ─── Department colour map ─────────────────────────────── */
const DEPT_COLORS = {
  FIRE_DEPARTMENT: "#e94560",
  POLICE: "#4a90d9",
  MUNICIPALITY: "#2ecc71",
};

const STATUS_LABELS = {
  OPEN: "OPEN",
  IN_PROGRESS: "RESPONDING",
  RESOLVED: "RESOLVED",
};

/* ─── Time-ago helper (local time diff from UTC timestamp) ── */
function timeAgo(dateStr) {
  if (!dateStr) return "";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ${mins % 60}m ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

/* ─── Main Landing Page ───────────────────────────────────── */
export default function LandingPage() {
  const navigate = useNavigate();
  const [incidents, setIncidents] = useState([]);
  const [landingStats, setLandingStats] = useState({ total: 0, resolved: 0 });

  useEffect(() => {
    API.get("/stats/live-feed?limit=5")
      .then((res) => setIncidents(res.data || []))
      .catch(() => setIncidents([]));

    API.get("/stats/global")
      .then((res) => {
        const d = res.data || {};
        const byStatus = d.by_status || {};
        setLandingStats({
          total: d.total_reports || 0,
          resolved: byStatus.RESOLVED || 0,
        });
      })
      .catch(() => {});
  }, []);

  return (
    <div className="landing">
      {/* ── Navbar ── */}
      <nav className="landing-nav">
        <div className="nav-brand">
          <img src={logo} alt="CityPulse" className="nav-logo" />
          <span className="nav-title">
            City<span className="accent">Pulse</span>
          </span>
        </div>
        <div className="nav-links">
          <a href="/dashboard">Dashboard</a>
          <a href="/chat/">Report</a>
          <a href="/stats">Statistics</a>
          <button className="nav-cta" onClick={() => navigate("/login")}>
            Sign In
          </button>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section id="home" className="landing-hero">
        <div className="hero-content">
          <h1 className="hero-headline">
            YOUR CITY,{" "}
            <span className="hero-highlight">CONNECTED</span>.
          </h1>
          <p className="hero-subtitle">Every Emergency, One Platform.</p>
          <p className="hero-description">
            Tell us what's happening in your city. Fire. Police.
            Infrastructure. Unified in real time, so your city never misses a
            beat.
          </p>
          <div className="hero-actions">
            <button
              className="btn-primary"
              onClick={() => { window.location.href = "/chat/"; }}
            >
              <span className="btn-icon">⊳</span> REPORT AN INCIDENT
            </button>
            <button
              className="btn-outline"
              onClick={() => navigate("/dashboard")}
            >
              <span className="btn-icon">⊳</span> EXPLORE OPEN INCIDENTS
            </button>
          </div>

          {/* Partner logos */}
          <div className="partner-strip">
            <span className="partner-label">Powered by</span>
            <div className="partner-logos">
              <div className="partner-logo-item">
                <img src={logo} alt="CityPulse" className="partner-logo" />
                <span>CityPulse</span>
              </div>
              <div className="partner-connector">
                <div className="connector-line" />
                <div className="connector-dot" />
                <div className="connector-line" />
              </div>
              <div className="partner-logo-item">
                <img src={mistralLogo} alt="Mistral AI" className="partner-logo partner-svg" />
                <span>Mistral AI</span>
              </div>
              <div className="partner-connector">
                <div className="connector-line" />
                <div className="connector-dot" />
                <div className="connector-line" />
              </div>
              <div className="partner-logo-item">
                <img src={awsLogo} alt="AWS" className="partner-logo partner-svg" />
                <span>AWS</span>
              </div>
            </div>
          </div>
        </div>

        {/* 3D Globe */}
        <div className="hero-globe">
          <Canvas
            camera={{ position: [0, 0, 5.5], fov: 45 }}
            style={{ width: "100%", height: "100%" }}
          >
            <Suspense fallback={null}>
              <EarthGlobe />
              <OrbitControls
                enableZoom={false}
                enablePan={false}
                autoRotate={false}
                minPolarAngle={Math.PI / 3}
                maxPolarAngle={Math.PI / 1.5}
              />
            </Suspense>
          </Canvas>

          {/* Floating partner badges at top-left of globe */}
          <div className="globe-floating-logos">
            <div className="globe-logo-badge">
              <img src={logo} alt="CityPulse" />
              <span>CityPulse</span>
            </div>
            <div className="globe-logo-connector" />
            <div className="globe-logo-badge">
              <img src={mistralLogo} alt="Mistral AI" />
              <span>Mistral</span>
            </div>
            <div className="globe-logo-connector" />
            <div className="globe-logo-badge">
              <img src={awsLogo} alt="AWS" />
              <span>AWS</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── Stats ── */}
      <section id="services" className="landing-stats">
        <StatCard value="99.99" suffix="%" label="Platform Availability" color="#00d4ff" />
        <StatCard value="3" suffix="" label="Services Connected" color="#e94560" />
        <StatCard value={String(landingStats.total)} suffix="" label="Incidents Reported" color="#6c63ff" />
        <StatCard value={String(landingStats.resolved)} suffix="" label="Incidents Resolved" color="#2ecc71" />
      </section>

      {/* ── Process ── */}
      <section id="process" className="landing-process">
        <h2 className="section-heading">
          <span className="heading-slash">//</span> Process
        </h2>
        <div className="process-steps">
          <ProcessStep
            number={1}
            title="Incident Reported"
            description="Citizens, or first responders submit via app, web, or API integration. The incident appears on the live command map in under a second."
            icon="📡"
          />
          <ProcessStep
            number={2}
            title="Classification & Routing to the correct Authority"
            description="CityPulse classifies and routes the report to the correct authority — fire departments, police departments, or municipalities — with full context and priority level."
            icon="🔀"
          />
          <ProcessStep
            number={3}
            title="Resolved & Recorded"
            description="Every response is logged. Status updates flow in real time. The full incident record is stored for accountability, analytics, and city-wide learning."
            icon="✅"
          />
        </div>
      </section>

      {/* ── Incident Stream ── */}
      <section id="incidents" className="landing-incidents">
        <h2 className="section-heading">
          <span className="heading-slash">//</span> Incident Stream{" "}
          <span className="live-badge">
            <span className="live-dot" /> LIVE
          </span>
        </h2>
        <div className="incident-list">
          {incidents.map((inc, i) => {
            const color = DEPT_COLORS[inc.department] || "#8a8fa8";
            const deptLabel = (inc.department || "").replace(/_/g, " ");
            return (
              <div
                key={inc.id || i}
                className="incident-row"
                style={{ borderColor: color }}
              >
                <div className="incident-dept" style={{ color }}>
                  {deptLabel}
                </div>
                <div className="incident-desc">{inc.title}</div>
                <div className="incident-divider" />
                <div className="incident-location">
                  <span className="loc-icon">📍</span> {inc.location}
                </div>
                <div className="incident-divider" />
                <div className="incident-time">{timeAgo(inc.created_at)}</div>
                <div
                  className="incident-status"
                  style={{ color }}
                >
                  {STATUS_LABELS[inc.status] || inc.status}
                </div>
              </div>
            );
          })}
          {incidents.length === 0 && (
            <p style={{ color: "#555a72", textAlign: "center", padding: "2rem" }}>
              No incidents reported yet.
            </p>
          )}
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="landing-footer">
        <div className="footer-brand">
          <img src={logo} alt="CityPulse" className="footer-logo" />
          <span>
            City<span className="accent">Pulse</span>
          </span>
        </div>
        <div className="footer-links">
          <a href="/dashboard">Dashboard</a>
          <a href="/chat/">Report</a>
          <a href="/stats">Statistics</a>
        </div>
        <p className="footer-copy">
          © 2026 CityPulse — Built with Mistral AI &amp; AWS
        </p>
      </footer>
    </div>
  );
}
