import { useState, useCallback, useEffect } from "react";
import Chat from "./Chat";
import Dashboard from "./Dashboard";
import PredictionView from "./PredictionView";
import "./App.css";

function getUserId(): string {
  let id = localStorage.getItem("runa_user_id");
  if (!id) {
    id = "user-" + Math.random().toString(36).slice(2, 10);
    localStorage.setItem("runa_user_id", id);
  }
  return id;
}

type Tab = "today" | "checkin" | "path" | "onboarding";

const NAV_ITEMS: { id: Tab; label: string }[] = [
  { id: "today", label: "Today" },
  { id: "checkin", label: "Check-in" },
  { id: "path", label: "Path" },
];

function App() {
  const userId = getUserId();
  const [tab, setTab] = useState<Tab>(() =>
    localStorage.getItem("runa_onboarded") ? "today" : "onboarding"
  );
  const [refreshKey, setRefreshKey] = useState(0);

  function handleOnboardingComplete() {
    localStorage.setItem("runa_onboarded", "true");
    setRefreshKey((k) => k + 1);
    setTab("today");
  }

  const switchTab = useCallback((t: Tab) => {
    if (t === "today") setRefreshKey((k) => k + 1);
    setTab(t);
  }, []);

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      if (detail === "checkin") switchTab("checkin");
    };
    window.addEventListener("runa-navigate", handler);
    return () => window.removeEventListener("runa-navigate", handler);
  }, [switchTab]);

  if (tab === "onboarding") {
    return (
      <div className="onboarding-shell">
        <Chat userId={userId} mode="onboarding" onComplete={handleOnboardingComplete} />
      </div>
    );
  }

  return (
    <div className="layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-logo">Runa</div>
          <div className="sidebar-tagline">Clarity for today</div>
        </div>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${tab === item.id ? "active" : ""}`}
              onClick={() => switchTab(item.id)}
            >
              <span className="nav-label">{item.label}</span>
            </button>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <main className="main">
        {tab === "today" && <Dashboard key={refreshKey} userId={userId} />}
        {tab === "checkin" && <Chat userId={userId} mode="checkin" onComplete={() => {}} />}
        {tab === "path" && <PredictionView userId={userId} />}
      </main>
    </div>
  );
}

export default App;
