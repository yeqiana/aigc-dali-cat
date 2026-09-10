import { useState } from 'react';
import { runtimeApi } from '../api/runtime';
import RuntimeTimeline from '../components/RuntimeTimeline';
import TraceGraph from '../components/TraceGraph';

export default function RuntimeVisualization() {
  const [runtime, setRuntime] = useState<any>();
  const [trace, setTrace] = useState<any>();

  async function load(id: string) {
    setRuntime(await runtimeApi.getExecutionRuntime(id));
    setTrace(await runtimeApi.getTrace(id));
  }

  return <div>
    <h2>Runtime Visualization</h2>
    <button onClick={() => load('demo-execution')}>Load Runtime</button>
    <RuntimeTimeline data={runtime} />
    <TraceGraph data={trace} />
  </div>;
}
