// Route-level permission gate for the dashboard shell. Hiding a nav link is not
// an authorization boundary, so the layout also checks the URL the user opened.
// (The API enforces the same permissions; this keeps the UI from rendering
// pages that would only show errors.) Pure and dependency-free so it can be
// unit-tested with `node --test`.
import { permissionSatisfied, type ModuleKey } from "@nodedr-restaurant/types";

export interface GatedRoute {
  href: string;
  permission?: string;
  requiredModule?: ModuleKey;
  superAdminOnly?: boolean;
}

export interface UserAccessContext {
  permissions: readonly string[];
  enabledModules?: readonly string[];
  isSuperAdmin?: boolean;
  licenseStatus?: string;
}

/** Permission and Module needed to open `pathname`, from the longest matching nav entry. */
export function routeEntryFor(pathname: string, routes: readonly GatedRoute[]): GatedRoute | undefined {
  let best: GatedRoute | undefined;
  for (const r of routes) {
    if (pathname === r.href || pathname.startsWith(`${r.href}/`)) {
      if (!best || r.href.length > best.href.length) best = r;
    }
  }
  return best;
}

export function requiredPermissionFor(pathname: string, routes: readonly GatedRoute[]): string | undefined {
  return routeEntryFor(pathname, routes)?.permission;
}

export function canOpen(
  pathname: string,
  userOrPermissions: UserAccessContext | readonly string[],
  routes: readonly GatedRoute[],
): boolean {
  const user: UserAccessContext = Array.isArray(userOrPermissions)
    ? { permissions: userOrPermissions }
    : (userOrPermissions as UserAccessContext);

  if (user.isSuperAdmin) return true;

  const entry = routeEntryFor(pathname, routes);
  if (!entry) return true;

  if (entry.superAdminOnly) {
    return Boolean(user.isSuperAdmin);
  }

  // Check module entitlement if required
  if (entry.requiredModule && user.enabledModules) {
    if (!user.enabledModules.includes(entry.requiredModule)) {
      return false;
    }
  }

  // Check permission
  if (entry.permission) {
    return permissionSatisfied(user.permissions, entry.permission);
  }

  return true;
}

/** Where to send someone who opened a page they cannot use (e.g. a waiter after login). */
export function firstAllowedHref(
  userOrPermissions: UserAccessContext | readonly string[],
  routes: readonly GatedRoute[],
): string | undefined {
  return routes.find((r) => canOpen(r.href, userOrPermissions, routes))?.href;
}

