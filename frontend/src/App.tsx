import { useState } from "react";
import Chat from "./Chat";
import Dashboard from "./Dashboard";
import "./App.css";

// Auto-generate userId for MVP (no auth)
function getUserId(): string {
  let id = localStorage.getItem("runa_user_id");
  if (!id) {
    id = "user-" + Math.random().toString(36).slice(2, 10);
    localStorage.setItem("runa_user_id", id);
  }
  return id;
}

type Screen = "onboarding" | "dashboard" | "checkin";

function App() {
  const userId = getUserId();

  const [screen, setScreen] = useState<Screen>(() => {
    return localStorage.getItem("runa_onboarded") ? "dashboard" : "onboarding";
  });

  function handleOnboardingComplete() {
    localStorage.setItem("runa_onboarded", "true");
    setScreen("dashboard");
  }

  return (
    <div className="app">
      {screen === "onboarding" && (
        <Chat
          userId={userId}
          mode="onboarding"
          onOnboardingComplete={handleOnboardingComplete}
        />
      )}

      {screen === "dashboard" && (
        <Dashboard
          userId={userId}
          onOpenCheckin={() => setScreen("checkin")}
        />
      )}

      {screen === "checkin" && (
        <Chat
          userId={userId}
          mode="checkin"
          onOnboardingComplete={() => {}}
        />
      )}

      {screen === "checkin" && (
        <button className="back-btn" onClick={() => setScreen("dashboard")}>
          ← Дашборд
        </button>
      )}
    </div>
  );
}

export default App;
