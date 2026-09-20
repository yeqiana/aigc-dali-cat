import { ReactNode } from 'react';

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div>
      <aside>
        <h2>Story OS V3</h2>
        <nav>
          <a href="/">Dashboard</a><br />
          <a href="/agents">Agents</a><br />
          <a href="/executions">Executions</a><br />
          <a href="/traces">Traces</a><br />
          <a href="/memory">Memory</a>
        </nav>
      </aside>
      <main>{children}</main>
    </div>
  );
}
