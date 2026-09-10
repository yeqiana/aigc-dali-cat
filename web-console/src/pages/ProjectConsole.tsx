import { useEffect, useState } from 'react';
import { projectApi } from '../api/project';

export default function ProjectConsole() {
  const [projects, setProjects] = useState<any[]>([]);

  useEffect(() => {
    projectApi.list().then(setProjects).catch(() => setProjects([]));
  }, []);

  return <section>
    <h2>Project Console</h2>
    {projects.map((project) => <div key={project.projectId}>{project.projectName}</div>)}
  </section>;
}
