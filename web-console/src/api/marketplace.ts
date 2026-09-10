import { apiClient } from './client';

export const marketplaceApi = {
  listAgents: () => apiClient.get('/api/v1/marketplace/agents'),
  listSkills: () => apiClient.get('/api/v1/marketplace/skills'),
  installSkill: (skillId: string) =>
    apiClient.post('/api/v1/marketplace/skills/install', { skillId }),
};
