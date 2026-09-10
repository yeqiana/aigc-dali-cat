import type { RuntimeStreamEvent } from '../types/streaming';

export function RuntimeStreamViewer({ events }: { events: RuntimeStreamEvent[] }) {
  return (
    <section>
      <h3>Live Runtime Stream</h3>
      {events.map((event) => (
        <div key={`${event.executionId}-${event.timestamp}`}>
          {event.timestamp} | {event.eventType} | {event.nodeName ?? event.nodeId} | {event.status}
        </div>
      ))}
    </section>
  );
}
