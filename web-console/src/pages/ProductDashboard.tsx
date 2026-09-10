import StatusCard from '../components/StatusCard';

export default function ProductDashboard() {
  return (
    <div>
      <h1>Story OS V3 Dashboard</h1>
      <StatusCard title="Agent Runtime" value="Ready" />
      <StatusCard title="Workflow" value="Online" />
      <StatusCard title="Memory System" value="Active" />
    </div>
  );
}
