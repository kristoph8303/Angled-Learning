import React, { useEffect, useState } from "react";
import {
  BrowserRouter,
  Navigate,
  NavLink,
  Outlet,
  Route,
  Routes,
  useNavigate,
} from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import LessonGenerator from "./pages/LessonGenerator";
import LessonPlayer from "./pages/LessonPlayer";
import AdminPanel from "./pages/AdminPanel";
import Login from "./Login";

import { getCurricula } from "./api/client";

function LoadingScreen() {
  return (
    <div className="loading-screen" role="status" aria-live="polite">
      <span className="spinner spinner-large" />
      <span>Loading Angled Learning…</span>
    </div>
  );
}

function ProtectedRoute({ user }) {
  return user ? <Outlet /> : <Navigate to="/login" replace />;
}

function AppShell({ user, onLogout, curricula }) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <NavLink className="brand" to="/dashboard">
          <span className="brand-mark">A</span>
          <span>Angled Learning</span>
        </NavLink>

        <nav className="main-nav" aria-label="Main navigation">
          <NavLink
            className={({ isActive }) =>
              isActive ? "nav-link active" : "nav-link"
            }
            to="/dashboard"
          >
            Dashboard
          </NavLink>

          <NavLink
            className={({ isActive }) =>
              isActive ? "nav-link active" : "nav-link"
            }
            to="/generate"
          >
            Generate
          </NavLink>

          <NavLink
            className={({ isActive }) =>
              isActive ? "nav-link active" : "nav-link"
            }
            to="/admin"
          >
            Admin
          </NavLink>
        </nav>

        <div className="user-menu">
          <span className="user-name">{user.name}</span>

          <button
            className="button button-ghost button-small"
            onClick={onLogout}
          >
            Logout
          </button>
        </div>
      </header>

      <main className="page-container">
        <Outlet context={{ curricula, user }} />
      </main>
    </div>
  );
}

function AppRoutes({
  user,
  setUser,
  curricula,
  loading,
  error,
}) {
  const navigate = useNavigate();

  function handleLogout() {
    setUser(null);
    navigate("/login");
  }

  if (loading) {
    return <LoadingScreen />;
  }

  if (error) {
    return (
      <div className="loading-screen">
        <div className="error-card">
          <h1>Unable to load curriculum data</h1>
          <p>{error}</p>

          <button
            className="button"
            onClick={() => window.location.reload()}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={
          user ? (
            <Navigate to="/dashboard" replace />
          ) : (
            <Login onLogin={setUser} />
          )
        }
      />

      <Route element={<ProtectedRoute user={user} />}>
        <Route
          element={
            <AppShell
              user={user}
              onLogout={handleLogout}
              curricula={curricula}
            />
          }
        >
          <Route path="/dashboard" element={<Dashboard />} />

          <Route
            path="/generate"
            element={<LessonGenerator />}
          />

          <Route
            path="/lesson/:id"
            element={<LessonPlayer />}
          />

          <Route
            path="/admin"
            element={<AdminPanel />}
          />
        </Route>
      </Route>

      <Route
        path="*"
        element={
          <Navigate
            to={user ? "/dashboard" : "/login"}
            replace
          />
        }
      />
    </Routes>
  );
}

export default function App() {
  const [user, setUser] = useState(() => {
    try {
      return (
        JSON.parse(
          localStorage.getItem("angled_user")
        ) || null
      );
    } catch {
      return null;
    }
  });

  const [curricula, setCurricula] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;

    getCurricula()
      .then((data) => {
        if (mounted) {
          setCurricula(data);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(
            err.message ||
              "Could not load curricula."
          );
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (user) {
      localStorage.setItem(
        "angled_user",
        JSON.stringify(user)
      );
    } else {
      localStorage.removeItem("angled_user");
    }
  }, [user]);

  return (
    <BrowserRouter>
      <AppRoutes
        user={user}
        setUser={setUser}
        curricula={curricula}
        loading={loading}
        error={error}
      />
    </BrowserRouter>
  );
}
