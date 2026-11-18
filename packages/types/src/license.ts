import { z } from "zod";

export const moduleKeyEnum = z.enum([
  "POS",
  "ORDERS",
  "TABLES",
  "RESERVATIONS",
  "MENU",
  "KDS",
  "CUSTOMERS",
  "INVENTORY",
  "DELIVERY",
  "TEAM",
  "ACCOUNTING",
  "REPORTS",
  "MARKETING",
  "OPERATIONS",
  "ATTENDANCE",
  "SETTINGS",
  "VERIFACTU",
  "INTEGRATIONS",
]);
export type ModuleKey = z.infer<typeof moduleKeyEnum>;

export const licenseStatusEnum = z.enum(["ACTIVE", "EXPIRED", "SUSPENDED"]);
export type LicenseStatus = z.infer<typeof licenseStatusEnum>;

export const updateLicenseSchema = z.object({
  status: licenseStatusEnum.optional(),
  validUntil: z.string().datetime().optional(),
  gracePeriodDays: z.number().int().min(0).max(90).optional(),
  maxBranches: z.number().int().min(1).max(1000).optional(),
  maxUsers: z.number().int().min(1).max(5000).optional(),
  enabledModules: z.array(moduleKeyEnum).optional(),
  notes: z.string().max(1000).optional(),
});
export type UpdateLicenseDto = z.infer<typeof updateLicenseSchema>;

export interface LicenseDto {
  id: string;
  restaurantId: string;
  status: LicenseStatus;
  validFrom: string;
  validUntil: string;
  gracePeriodDays: number;
  maxBranches: number;
  maxUsers: number;
  enabledModules: ModuleKey[];
  notes?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface SuperAdminRestaurantSummary {
  id: string;
  name: string;
  createdAt: string;
  ownerEmail?: string | null;
  ownerName?: string | null;
  branchCount: number;
  userCount: number;
  license?: LicenseDto | null;
}
