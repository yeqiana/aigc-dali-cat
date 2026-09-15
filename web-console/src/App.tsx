import { BrowserRouter, Link, Route, Routes } from 'react-router-dom';
import Agents from './pages/Agents';
import Dashboard from './pages/Dashboard';
import Memory from './pages/Memory';

function Layout() {
  return <div style={{padding: 24}}>
    <h1>Story OS V3 Console</h1>
    <nav>
      <Link to="/">Dashboard</Link> | <Link to="/agents">Agents</Link> | <Link to="/memory">Memory</Link>
    </nav>
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/agents" element={<Agents />} />
      <Route path="/memory" element={<Memory />} />
    </Routes>
  </div>;
}

export default function App() {
  return <BrowserRouter><Layout /></BrowserRouter>;
}
