import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";

import DashboardPage from "./pages/DashboardPage";
import ReportPage from "./pages/ReportPage";
import StatsPage from "./pages/StatsPage";

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />

          <Route
            path="/dashboard"
            element={
                <DashboardPage />
            }
          />
          <Route
            path="/report"
            element={
                <ReportPage />
            }
          />
          <Route
            path="/stats"
            element={
                <StatsPage />
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
