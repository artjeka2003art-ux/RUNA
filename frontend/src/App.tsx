import { useState, useCallback, useEffect } from "react";
import Chat from "./Chat";
import Dashboard from "./Dashboard";
import PredictionView from "./PredictionView";
import LifeMap from "./LifeMap";
import SphereDetail from "./SphereDetail";
import Reveal from "./Reveal";
import { createSphere } from "./api";
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

/** Where to return after leaving sphere-detail */
type SphereOrigin = "lifemap" | "workspace";

const NAV_ITEMS: { id: Tab; label: string }[] = [
  { id: "today", label: "Today" },
  { id: "lifemap", label: "Life Map" },
  { id: "path", label: "Decisions" },
];

export interface DecisionBridge {
  source_tension: string;
  draft_question: string;
  draft_variants: string[];
  bridge_reason: string;
}

export interface RevealData {
  spheres: { id: string; name: string; score?: number }[];
  lifeScore: number;
  activeTensions?: { name: string; description: string; spheres?: string[] }[];
  decisionBridge?: DecisionBridge;
}

/** Context passed from workspace to sphere detail */
export interface WorkspaceSphereContext {
  missingWhat: string;
  missingWhy: string;
  question?: string;
  allMissing?: { what: string; why: string }[];
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
  const [sphereOrigin, setSphereOrigin] = useState<SphereOrigin>("lifemap");
  const [workspaceSphereCtx, setWorkspaceSphereCtx] = useState<WorkspaceSphereContext | null>(null);
  const [returnedFromSphere, setReturnedFromSphere] = useState(false);
  const [decisionBridge, setDecisionBridge] = useState<DecisionBridge | null>(null);

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
    setSphereOrigin("lifemap");
    setWorkspaceSphereCtx(null);
    setTab("sphere-detail");
  }

  /** Called from workspace when user clicks a missing-context sphere hint */
  function handleOpenSphereFromWorkspace(
    sphereId: string,
    ctx: WorkspaceSphereContext,
  ) {
    setSelectedSphereId(sphereId);
    setSphereIntro(null);
    setSphereOrigin("workspace");
    setWorkspaceSphereCtx(ctx);
    setTab("sphere-detail");
  }

  /** Called from workspace when user clicks "create new sphere" for missing context */
  async function handleCreateSphereAndNavigate(
    sphereName: string,
    ctx: WorkspaceSphereContext,
  ) {
    try {
      const res = await createSphere(userId, sphereName);
      const newSphereId = res?.data?.sphere?.id;
      if (newSphereId) {
        setSelectedSphereId(newSphereId);
        setSphereIntro(null);
        setSphereOrigin("workspace");
        setWorkspaceSphereCtx(ctx);
        setTab("sphere-detail");
      }
    } catch {
      /* creation failed — stay on workspace */
    }
  }

  function handleBackFromSphere() {
    const origin = sphereOrigin;
    setSelectedSphereId(null);
    setSphereIntro(null);
    setWorkspaceSphereCtx(null);
    if (origin === "workspace") {
      setReturnedFromSphere(true);
      setTab("path");
    } else {
      setRefreshKey((k) => k + 1);
      setTab("lifemap");
    }
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
    return (
      <Reveal
        data={revealData}
        onContinue={handleRevealContinue}
        onGoToDecisions={() => {
          if (revealData?.decisionBridge) {
            setDecisionBridge(revealData.decisionBridge);
          }
          setRefreshKey((k) => k + 1);
          setTab("path");
        }}
      />
    );
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
        {tab === "path" && (
          <PredictionView
            userId={userId}
            onNavigateToSphere={handleOpenSphereFromWorkspace}
            onCreateSphereAndNavigate={handleCreateSphereAndNavigate}
            returnedFromSphere={returnedFromSphere}
            onClearReturned={() => setReturnedFromSphere(false)}
            decisionBridge={decisionBridge}
            onClearBridge={() => setDecisionBridge(null)}
          />
        )}
        {tab === "sphere-detail" && selectedSphereId && (
          <SphereDetail
            userId={userId}
            sphereId={selectedSphereId}
            intro={sphereIntro}
            onBack={handleBackFromSphere}
            workspaceContext={workspaceSphereCtx}
          />
        )}
      </main>
    </div>
  );
}

export default App;
