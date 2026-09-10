import type { RuntimeState } from '../types/monitoring';

export function RuntimeMonitor({ state }: { state?: RuntimeState }) {
  return (
    <section>
      <h3>Realtime Runtime Monitor</h3>
      <div>Status: {state?.status ?? 'UNKNOWN'}</div>
      <div>Step: {state?.currentStep ?? '-'}</div>
      <div>Worker: {state?.workerId ?? '-'}</div>
    </section>
  );
}
