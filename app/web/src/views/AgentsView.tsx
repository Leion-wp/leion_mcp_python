import React, { useState } from "react";
import { useWidgetState } from "../hooks/useWidgetState";

declare global {
  interface Window {
    openai?: any;
  }
}

interface AgentPlan {
  plan_id?: string;
  steps: { id: string; title: string; status: string }[];
}

interface WidgetAgentState {
  currentPlan?: AgentPlan;
  lastGoal?: string;
}

export function AgentsView() {
  const [goalInput, setGoalInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [widgetState, setWidgetState] = useWidgetState<WidgetAgentState>(() => ({}));

  const plan = widgetState?.currentPlan;

  const proposePlan = async () => {
    if (!window.openai?.callTool || !goalInput.trim()) return;
    setLoading(true);
    try {
      const res = await window.openai.callTool("leion_cc_agents", {
        mode: "draft_plan",
        goal: goalInput.trim(),
      });
      const sc = res?.structuredContent;
      if (sc?.type === "leion_agent_plan") {
        setWidgetState({
          currentPlan: sc.plan,
          lastGoal: goalInput.trim(),
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const executeStep = async (stepId: string) => {
    if (!window.openai?.callTool || !plan) return;
    setLoading(true);
    try {
      const res = await window.openai.callTool("leion_cc_agents", {
        mode: "execute_step",
        plan,
        step_id: stepId,
      });
      const sc = res?.structuredContent;
      if (sc?.type === "leion_agent_plan") {
        setWidgetState((prev) => ({
          ...(prev ?? {}),
          currentPlan: sc.plan,
        }));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div>
        <label>
          Goal:
          <input
            type="text"
            value={goalInput}
            onChange={(e) => setGoalInput(e.target.value)}
            style={{ width: "100%", marginTop: 4 }}
          />
        </label>
        <button onClick={proposePlan} disabled={loading || !goalInput.trim()}>
          {loading ? "En cours..." : "Proposer un plan"}
        </button>
      </div>

      {plan && (
        <section>
          <h3>Plan courant</h3>
          <ul>
            {plan.steps?.map((s) => (
              <li key={s.id} style={{ marginBottom: 4 }}>
                <strong>[{s.status}]</strong> {s.title}{" "}
                {s.status !== "done" && (
                  <button onClick={() => executeStep(s.id)} disabled={loading}>
                    Exécuter
                  </button>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
