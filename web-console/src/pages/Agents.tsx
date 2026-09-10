import { useEffect, useState } from 'react';
import { agentApi } from '../api/agent';

export default function Agents() {
  const [executions, setExecutions] = useState<unknown[]>([]);

  useEffect(() => {
    agentApi.listExecutions('default').then(setExecutions).catch(() => setExecutions([]));
  }, []);

  return (
    <section>
      <h2>Agent Console</h2>
      <p>Execution Records: {executions.length}</p>
    </section>
  );
}
