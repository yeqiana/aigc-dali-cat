export default function StatusCard({ title, value }: { title: string; value: string | number }) {
  return (
    <section>
      <h3>{title}</h3>
      <strong>{value}</strong>
    </section>
  );
}
