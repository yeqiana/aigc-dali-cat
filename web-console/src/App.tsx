import { BrowserRouter, Link, Route, Routes } from 'react-router-dom';

function Layout() {
  return <div style={{padding: 24}}>
    <h1>Story OS V3 Console</h1>
    <nav>
      <Link to="/">Dashboard</Link> | <Link to="/agents">Agents</Link> | <Link to="/workflows">Workflows</Link> | <Link to="/memory">Memory</Link>
    </nav>
    <Routes>
      <Route path="/" element={<h2>Dashboard</h2>} />
      <Route path="/agents" element={<h2>Agent Console</h2>} />
      <Route path="/workflows" element={<h2>Workflow Console</h2>} />
      <Route path="/memory" element={<h2>Memory Console</h2>} />
    </Routes>
  </div>;
}

export default function App() {
  return <BrowserRouter><Layout /></BrowserRouter>;
}
