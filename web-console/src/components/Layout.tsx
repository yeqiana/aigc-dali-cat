import { ReactNode } from 'react';
import { Link } from 'react-router-dom';

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div>
      <aside>
        <h2>Story OS V3</h2>
        <nav>
          <Link to="/">Dashboard</Link><br />
          <Link to="/agents">Agents</Link><br />
          <Link to="/executions">Executions</Link><br />
          <Link to="/traces">Traces</Link><br />
          <Link to="/memory">Memory</Link>
        </nav>
      </aside>
      <main>{children}</main>
    </div>
  );
}
