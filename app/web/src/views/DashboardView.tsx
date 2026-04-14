import React from "react";

interface DashboardProps {
  data?: any;
}

export function DashboardView({ data }: DashboardProps) {
  if (!data || data.type !== "leion_dashboard") {
    return <div>Aucune donnée dashboard (appelle leion_cc_dashboard).</div>;
  }

  const { health, projects, workflows, recent_events } = data;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <section>
        <h3>Health</h3>
        <pre style={{ fontSize: 12 }}>{JSON.stringify(health, null, 2)}</pre>
      </section>

      <section>
        <h3>Projets</h3>
        <ul>
          {projects?.map((p: any) => (
            <li key={p.id}>
              <strong>{p.id}</strong> – {p.status} – {p.summary}
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h3>Workflows</h3>
        <div>Total : {workflows?.count ?? 0}</div>
      </section>

      <section>
        <h3>Derniers événements</h3>
        <ul>
          {recent_events?.map((e: any, idx: number) => (
            <li key={idx}>
              [{e.ts}] {e.type} – {e.message}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
