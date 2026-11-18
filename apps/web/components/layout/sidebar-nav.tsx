"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { SessionUser } from "@nodedr-restaurant/types";
import { hasPermission } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";
import { useI18n } from "@/lib/i18n/context";
import { useNavBadges } from "@/hooks/use-nav-badges";
import { NavDot } from "./nav-dot";
import { NAV_ITEMS } from "./nav-items";

export function SidebarNav({
  user,
  onNavigate,
  collapsed = false,
}: {
  user?: SessionUser;
  onNavigate?: () => void;
  collapsed?: boolean;
}) {
  const pathname = usePathname();
  const { t } = useI18n();
  const badges = useNavBadges();

  const accessContext = user
    ? {
        permissions: user.permissions ?? [],
        enabledModules: user.enabledModules ?? [],
        isSuperAdmin: user.isSuperAdmin,
        licenseStatus: user.licenseStatus,
      }
    : undefined;

  const visibleItems = NAV_ITEMS.filter((item) => {
    if (item.superAdminOnly && !user?.isSuperAdmin) return false;
    if (user?.isSuperAdmin) return true;
    if (item.requiredModule && !(user?.enabledModules ?? []).includes(item.requiredModule)) {
      return false;
    }
    return !item.permission || hasPermission(user, item.permission);
  });

  return (
    <nav className={cn("flex flex-col gap-1", collapsed ? "px-2" : "px-3")}>
      {visibleItems.map(
        (item) => {
          const isActive = pathname?.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              title={collapsed ? t(item.labelKey) : undefined}
              aria-label={collapsed ? t(item.labelKey) : undefined}
              aria-current={isActive ? "page" : undefined}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                collapsed && "justify-center px-0",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground",
              )}
            >
              <Icon className="h-[18px] w-[18px] shrink-0" strokeWidth={2} />
              {!collapsed && t(item.labelKey)}
              {badges.nav[item.href] && !isActive ? <NavDot /> : null}
            </Link>
          );
        },
      )}
    </nav>
  );
}
