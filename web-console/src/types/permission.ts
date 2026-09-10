export interface TenantContext {
  tenantId: string;
  tenantName: string;
}

export interface UserContext {
  userId: string;
  username: string;
  roles: string[];
}

export interface Permission {
  resource: string;
  actions: string[];
}
