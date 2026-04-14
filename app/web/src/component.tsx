import React from "react";
import ReactDOM from "react-dom/client";
import { useOpenAiGlobal } from "./hooks/useOpenAiGlobal";
import { useWidgetState } from "./hooks/useWidgetState";
import { DashboardView } from "./views/DashboardView";
import { WorkflowsView } from "./views/WorkflowsView";
import { AgentsView } from "./views/AgentsView";

type Tab = "dashboard" | "workflows" | "agents";

function App() {
  const toolOutput = useOpenAiGlobal<any>("toolOutput");
  const [widgetState, setWidgetState] = useWidgetState<{ activeTab: Tab }>(() => ({
    activeTab: "dashboard",
  }));

  const activeTab = widgetState?.activeTab ?? "dashboard";

  const switchTab = (tab: Tab) => {
    setWidgetState((prev) => ({
      ...(prev ?? {}),
      activeTab: tab,
    }));
  };

  return (
    <div style={{ fontFamily: "system-ui", padding: 12, fontSize: 14 }}>
      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <button
          onClick={() => switchTab("dashboard")}
          style={{ fontWeight: activeTab === "dashboard" ? "bold" : "normal" }}
        >
          Dashboard
        </button>
        <button
          onClick={() => switchTab("workflows")}
          style={{ fontWeight: activeTab === "workflows" ? "bold" : "normal" }}
        >
          Workflows
        </button>
        <button
          onClick={() => switchTab("agents")}
          style={{ fontWeight: activeTab === "agents" ? "bold" : "normal" }}
        >
          Agents
        </button>
      </div>

      {activeTab === "dashboard" && (
        <DashboardView data={toolOutput?.structuredContent} />
      )}
      {activeTab === "workflows" && <WorkflowsView />}
      {activeTab === "agents" && <AgentsView />}
    </div>
  );
}

const rootEl = document.getElementById("root")!;
const root = ReactDOM.createRoot(rootEl);
root.render(<App />);
