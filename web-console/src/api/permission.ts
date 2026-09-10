import { apiClient } from './client';
import type { TenantContext, UserContext, Permission } from '../types/permission';

export const permissionApi = {
  getTenant(): Promise<TenantContext> {
    return apiClient.get('/api/v1/tenant');
  },
  getCurrentUser(): Promise<UserContext> {
    return apiClient.get('/api/v1/users/me');
  },
  getPermissions(): Promise<Permission[]> {
    return apiClient.get('/api/v1/permissions');
  },
};
