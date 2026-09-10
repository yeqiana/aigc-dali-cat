import { useState } from 'react';
import { executionApi } from '../api/execution';

export default function ExecutionExplorer() {
  const [id, setId] = useState('');
  const [execution, setExecution] = useState<any>(null);

  async function load() {
    if (!id) return;
    setExecution(await executionApi.get(id));
  }

  return (
    <section>
      <h2>Execution Explorer</h2>
      <input value={id} onChange={(e) => setId(e.target.value)} placeholder="execution id" />
      <button onClick={load}>Query</button>
      <pre>{JSON.stringify(execution, null, 2)}</pre>
    </section>
  );
}
