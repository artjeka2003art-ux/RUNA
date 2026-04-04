import { useState, useCallback, useEffect } from "react";
import Chat from "./Chat";
import Dashboard from "./Dashboard";
import PredictionView from "./PredictionView";
import LifeMap from "./LifeMap";
import SphereDetail from "./SphereDetail";
import Reveal from "./Reveal";
import "./App.css";

function getUserId(): string {
  let id = localStorage.getItem("runa_user_id");
  if (!id) {
    id = "user-" + Math.random().toString(36).slice(2, 10);
    localStorage.setItem("runa_user_id", id);
  }
  return id;
}

type Tab = "today" | "lifemap" | "path" | "onboarding" | "reveal" | "sphere-detail" | "checkin";

const NAV_ITEMS: { id: Tab; label: string }[] = [
  { id: "today", label: "Today" },
  { id: "lifemap", label: "Life Map" },
  { id: "path", label: "Path" },
];

export interface RevealData {
  spheres: { id: string; name: string; score?: number }[];
  lifeScore: number;
}

function App() {
  const userId = getUserId();
  const [tab, setTab] = useState<Tab>(() =>
    localStorage.getItem("runa_onboarded") ? "today" : "onboarding"
  );
  const [refreshKey, setRefreshKey] = useState(0);
  const [revealData, setRevealData] = useState<RevealData | null>(null);
  const [selectedSphereId, setSelectedSphereId] = useState<string | null>(null);
  const [sphereIntro, setSphereIntro] = useState<string | null>(null);

  function handleOnboardingComplete(data?: RevealData) {
    localStorage.setItem("runa_onboarded", "true");
    if (data && data.spheres.length > 0) {
      setRevealData(data);
      setTab("reveal");
    } else {
      setRefreshKey((k) => k + 1);
      setTab("today");
    }
  }

  function handleRevealContinue() {
    setRefreshKey((k) => k + 1);
    setTab("lifemap");
  }

  function handleOpenSphere(sphereId: string, intro?: string) {
    setSelectedSphereId(sphereId);
    setSphereIntro(intro || null);
    setTab("sphere-detail");
  }

  function handleBackFromSphere() {
    setSelectedSphereId(null);
    setSphereIntro(null);
    setRefreshKey((k) => k + 1);
    setTab("lifemap");
  }

  const switchTab = useCallback((t: Tab) => {
    if (t === "today" || t === "lifemap") setRefreshKey((k) => k + 1);
    setTab(t);
  }, []);

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      if (detail === "checkin") switchTab("checkin");
      if (detail === "lifemap") switchTab("lifemap");
      if (typeof detail === "object" && detail?.tab === "sphere-detail" && detail?.sphereId) {
        handleOpenSphere(detail.sphereId);
      }
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

  if (tab === "reveal" && revealData) {
    return <Reveal data={revealData} onContinue={handleRevealContinue} />;
  }

  const showSidebar = tab !== "sphere-detail";

  return (
    <div className="layout">
      {showSidebar && (
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
      )}

      <main className="main">
        {tab === "today" && <Dashboard key={refreshKey} userId={userId} />}
        {tab === "checkin" && <Chat userId={userId} mode="checkin" onComplete={() => {}} />}
        {tab === "lifemap" && (
          <LifeMap key={refreshKey} userId={userId} onOpenSphere={handleOpenSphere} />
        )}
        {tab === "path" && <PredictionView userId={userId} />}
        {tab === "sphere-detail" && selectedSphereId && (
          <SphereDetail
            userId={userId}
            sphereId={selectedSphereId}
            intro={sphereIntro}
            onBack={handleBackFromSphere}
          />
        )}
      </main>
    </div>
  );
}

export default App;
