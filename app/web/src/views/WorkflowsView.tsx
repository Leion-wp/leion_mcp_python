import React, { useEffect, useState } from "react";

declare global {
  interface Window {
    openai?: any;
  }
}

interface Workflow {
  id: string;
  name: string;
  tags?: string[];
  description?: string;
  has_required_inputs?: boolean;
}

export function WorkflowsView() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(false);
  const [runningId, setRunningId] = useState<string | null>(null);
  const [lastRun, setLastRun] = useState<any | null>(null);

  const loadWorkflows = async () => {
    if (!window.openai?.callTool) return;
    setLoading(true);
    try {
      const res = await window.openai.callTool("leion_cc_workflows", {
        include_definitions: false,
      });
      const sc = res?.structuredContent;
      if (sc?.type === "leion_workflows") {
        setWorkflows(sc.workflows ?? []);
      }
    } finally {
      setLoading(false);
    }
  };

  const runWorkflow = async (id: string) => {
    if (!window.openai?.callTool) return;
    setRunningId(id);
    try {
      const res = await window.openai.callTool("leion_cc_run_workflow", {
        workflow_id: id,
        inputs: {},
      });
      setLastRun(res?.structuredContent);
    } finally {
      setRunningId(null);
    }
  };

  useEffect(() => {
    loadWorkflows();
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div>
        <button onClick={loadWorkflows} disabled={loading}>
          {loading ? "Chargement..." : "Recharger les workflows"}
        </button>
      </div>

      <ul>
        {workflows.map((wf) => (
          <li key={wf.id} style={{ marginBottom: 8 }}>
            <div>
              <strong>{wf.name}</strong> ({wf.id})
            </div>
            {wf.tags && wf.tags.length > 0 && (
              <div>Tags: {wf.tags.join(", ")}</div>
            )}
            <div>{wf.description}</div>
            <button onClick={() => runWorkflow(wf.id)} disabled={runningId === wf.id}>
              {runningId === wf.id ? "En cours..." : "Run"}
            </button>
          </li>
        ))}
      </ul>

      {lastRun && (
        <section>
          <h3>Dernière exécution</h3>
          <pre style={{ fontSize: 12 }}>{JSON.stringify(lastRun, null, 2)}</pre>
        </section>
      )}
    </div>
  );
}
