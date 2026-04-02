/**
 * Check-in result view model.
 * Reads structured checkin_summary from backend — no regex guessing.
 */

export interface CheckinSummaryVM {
  updates: string[];
  concerns: string[];
  scoreDelta: number | null;
  newScore: number | null;
  weightsUpdated: number;
  nodesCreated: number;
  resolved: number;
}

export function buildCheckinSummary(data: any): CheckinSummaryVM | undefined {
  const summary = data?.checkin_summary;
  if (!summary) {
    // No summary at all — check if we at least have a score
    const score = data?.life_score;
    if (!score) return undefined;
    return {
      updates: [],
      concerns: [],
      scoreDelta: score.score_delta ?? null,
      newScore: score.total ?? null,
      weightsUpdated: 0,
      nodesCreated: 0,
      resolved: 0,
    };
  }

  return {
    updates: (summary.updates || []).slice(0, 5),
    concerns: (summary.concerns || []).slice(0, 3),
    scoreDelta: summary.score_delta ?? null,
    newScore: summary.new_score ?? null,
    weightsUpdated: summary.weights_updated ?? 0,
    nodesCreated: summary.nodes_created ?? 0,
    resolved: summary.resolved ?? 0,
  };
}
