import { useEffect, useState } from 'react';
import { marketplaceApi } from '../api/marketplace';

export default function MarketplaceConsole() {
  const [skills, setSkills] = useState<any[]>([]);

  useEffect(() => {
    marketplaceApi.listSkills().then(setSkills);
  }, []);

  return <div>
    <h2>Agent / Skill Marketplace</h2>
    {skills.map((skill) => (
      <div key={skill.skillId}>{skill.name}</div>
    ))}
  </div>;
}
