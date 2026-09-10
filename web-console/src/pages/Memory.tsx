import { useState } from 'react';
import { memoryApi } from '../api/memory';

export default function Memory() {
  const [count, setCount] = useState(0);

  async function search() {
    const result = await memoryApi.search({ query: 'story' });
    setCount(Array.isArray(result) ? result.length : 0);
  }

  return (
    <section>
      <h2>Memory Console</h2>
      <button onClick={search}>Search</button>
      <p>Results: {count}</p>
    </section>
  );
}
