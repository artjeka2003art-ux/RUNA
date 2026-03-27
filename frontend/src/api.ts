const BASE = "http://localhost:8000/api";

export async function startOnboarding(userId: string) {
  const res = await fetch(`${BASE}/onboarding/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  });
  return res.json();
}

export async function sendOnboardingMessage(
  userId: string,
  sessionId: string,
  message: string
) {
  const res = await fetch(`${BASE}/onboarding/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, session_id: sessionId, message }),
  });
  return res.json();
}

export async function sendCheckinMessage(userId: string, message: string) {
  const res = await fetch(`${BASE}/checkin/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, message }),
  });
  return res.json();
}

export async function getLifeScore(userId: string) {
  const res = await fetch(`${BASE}/dashboard/${userId}/score`);
  return res.json();
}

export async function getGraph(userId: string) {
  const res = await fetch(`${BASE}/dashboard/${userId}/graph`);
  return res.json();
}
