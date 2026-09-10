type TraceNode = {
  id: string;
  type: string;
};

export default function TraceGraph({ nodes }: { nodes: TraceNode[] }) {
  return <div>
    <h3>Trace Graph</h3>
    {nodes.map((node) => (
      <div key={node.id}>{node.type}: {node.id}</div>
    ))}
  </div>;
}
