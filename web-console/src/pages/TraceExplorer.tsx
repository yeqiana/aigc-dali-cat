import { useState } from 'react';
import { traceApi } from '../api/trace';

export default function TraceExplorer() {
  const [id, setId] = useState('');
  const [trace, setTrace] = useState<any>(null);

  async function load() {
    if (!id) return;
    setTrace(await traceApi.get(id));
  }

  return (
    <section>
      <h2>Trace Explorer</h2>
      <input value={id} onChange={(e) => setId(e.target.value)} placeholder="trace id" />
      <button onClick={load}>Query</button>
      <pre>{JSON.stringify(trace, null, 2)}</pre>
    </section>
  );
}
