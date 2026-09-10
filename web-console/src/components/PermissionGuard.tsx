import type { ReactNode } from 'react';

interface Props {
  action: string;
  permissions: string[];
  children: ReactNode;
}

export function PermissionGuard({ action, permissions, children }: Props) {
  if (!permissions.includes(action)) {
    return <span>Permission denied</span>;
  }

  return <>{children}</>;
}
