export interface MarketplaceAgent {
  agentId: string;
  name: string;
  description: string;
  status: string;
}

export interface MarketplaceSkill {
  skillId: string;
  name: string;
  capability: string;
  version: string;
}
