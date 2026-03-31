import { useState, useCallback } from "react";
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

type Tab = "home" | "checkin" | "prediction" | "onboarding";

const NAV_ITEMS: { id: Tab; label: string; icon: string }[] = [
  { id: "home", label: "Главная", icon: "⬡" },
  { id: "checkin", label: "Чекин", icon: "◉" },
  { id: "prediction", label: "Prediction", icon: "◈" },
];

function App() {
  const userId = getUserId();
  const [tab, setTab] = useState<Tab>(() =>
    localStorage.getItem("runa_onboarded") ? "home" : "onboarding"
  );
  const [refreshKey, setRefreshKey] = useState(0);

  function handleOnboardingComplete() {
    localStorage.setItem("runa_onboarded", "true");
    setRefreshKey((k) => k + 1);
    setTab("home");
  }

  const switchTab = useCallback((t: Tab) => {
    if (t === "home") setRefreshKey((k) => k + 1);
    setTab(t);
  }, []);

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
        <div className="sidebar-logo">R</div>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${tab === item.id ? "active" : ""}`}
              onClick={() => switchTab(item.id)}
              title={item.label}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </button>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <main className="main">
        {tab === "home" && <Dashboard key={refreshKey} userId={userId} />}
        {tab === "checkin" && <Chat userId={userId} mode="checkin" onComplete={() => {}} />}
        {tab === "prediction" && <PredictionView userId={userId} />}
      </main>
    </div>
  );
}

export default App;
