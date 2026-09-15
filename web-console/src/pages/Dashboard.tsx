import { useEffect, useState } from 'react';
import { apiGet } from '../api/client';

type Health = { status?: string };

export default function Dashboard() {
  const [status, setStatus] = useState('CHECKING');

  useEffect(() => {
    apiGet<Health>('/healthz')
      .then((row) => setStatus(row.status ?? 'UNKNOWN'))
      .catch(() => setStatus('DOWN'));
  }, []);

  return (
    <section>
      <h2>Dashboard</h2>
      <p>Story OS V3 Runtime Overview</p>
      <p>Platform API: {status}</p>
      <p>当前 Console 只展示已接入真实后端能力；未实现的 Workflow/Marketplace/Plugin 不进入主导航。</p>
    </section>
  );
}
