import {
  CalendarClock,
  Clock,
  Bike,
  Truck,
  Users,
  Landmark,
  BarChart3,
  Megaphone,
  Wrench,
  ChefHat,
  LayoutDashboard,
  ClipboardList,
  LayoutGrid,
  Package,
  Settings,
  ShoppingCart,
  UsersRound,
  UtensilsCrossed,
  ShieldAlert,
  type LucideIcon,
} from "lucide-react";
import type { ModuleKey } from "@nodedr-restaurant/types";

export interface NavItem {
  labelKey: string;
  href: string;
  icon: LucideIcon;
  permission?: string;
  requiredModule?: ModuleKey;
  superAdminOnly?: boolean;
}

export const NAV_ITEMS: NavItem[] = [
  { labelKey: "nav.dashboard", href: "/dashboard", icon: LayoutDashboard, permission: "dashboard.sales.view" },
  { labelKey: "nav.pos", href: "/pos", icon: ShoppingCart, permission: "orders.create", requiredModule: "POS" },
  { labelKey: "nav.orders", href: "/orders", icon: ClipboardList, permission: "orders.create", requiredModule: "ORDERS" },
  { labelKey: "nav.tables", href: "/tables", icon: LayoutGrid, permission: "tables.view", requiredModule: "TABLES" },
  {
    labelKey: "nav.reservations",
    href: "/reservations",
    icon: CalendarClock,
    permission: "reservations.manage",
    requiredModule: "RESERVATIONS",
  },
  { labelKey: "nav.menu", href: "/menu", icon: UtensilsCrossed, permission: "menu.view", requiredModule: "MENU" },
  { labelKey: "nav.kds", href: "/kds", icon: ChefHat, permission: "kds.manage", requiredModule: "KDS" },
  { labelKey: "nav.customers", href: "/customers", icon: UsersRound, permission: "customers.manage", requiredModule: "CUSTOMERS" },
  { labelKey: "nav.inventory", href: "/inventory", icon: Package, permission: "inventory.manage", requiredModule: "INVENTORY" },
  { labelKey: "nav.myDeliveries", href: "/my-deliveries", icon: Bike, permission: "delivery.rider", requiredModule: "DELIVERY" },
  { labelKey: "nav.delivery", href: "/delivery", icon: Truck, permission: "delivery.manage", requiredModule: "DELIVERY" },
  { labelKey: "nav.team", href: "/team", icon: Users, permission: "staff.manage", requiredModule: "TEAM" },
  { labelKey: "nav.accounting", href: "/accounting", icon: Landmark, permission: "accounting.manage", requiredModule: "ACCOUNTING" },
  { labelKey: "nav.reports", href: "/reports", icon: BarChart3, permission: "reports.access", requiredModule: "REPORTS" },
  { labelKey: "nav.marketing", href: "/marketing", icon: Megaphone, permission: "marketing.manage", requiredModule: "MARKETING" },
  { labelKey: "nav.operations", href: "/operations", icon: Wrench, permission: "operations.manage", requiredModule: "OPERATIONS" },
  { labelKey: "nav.attendance", href: "/attendance", icon: Clock, requiredModule: "ATTENDANCE" },
  { labelKey: "nav.settings", href: "/settings", icon: Settings, permission: "settings.manage", requiredModule: "SETTINGS" },
  { labelKey: "SuperAdmin Licenses", href: "/admin/licenses", icon: ShieldAlert, superAdminOnly: true },
];
