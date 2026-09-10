type RuntimeStep = {
  name: string;
  status: string;
};

export default function RuntimeTimeline({ steps }: { steps: RuntimeStep[] }) {
  return <div>
    <h3>Runtime Timeline</h3>
    <ol>
      {steps.map((step, index) => (
        <li key={index}>{step.name} - {step.status}</li>
      ))}
    </ol>
  </div>;
}
