"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "@/lib/api";
import { toast } from "@/lib/toast";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  ShieldAlert,
  Building2,
  Calendar,
  Users,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  SlidersHorizontal,
} from "lucide-react";
import type {
  SuperAdminRestaurantSummary,
  ModuleKey,
  LicenseStatus,
  UpdateLicenseDto,
} from "@nodedr-restaurant/types";

const ALL_MODULES: { key: ModuleKey; label: string; desc: string }[] = [
  { key: "POS", label: "Point of Sale (POS)", desc: "Checkout, billing & cash register" },
  { key: "ORDERS", label: "Orders Management", desc: "Live order tracking and fulfillment" },
  { key: "TABLES", label: "Floor & Tables", desc: "Table visual layout and live sessions" },
  { key: "RESERVATIONS", label: "Reservations", desc: "Table booking and waitlist" },
  { key: "MENU", label: "Menu Catalog", desc: "Items, variants, modifiers and categories" },
  { key: "KDS", label: "Kitchen Display (KDS)", desc: "Cook stations and kitchen tickets" },
  { key: "CUSTOMERS", label: "Customer CRM", desc: "Customer history, profiles and notes" },
  { key: "INVENTORY", label: "Inventory & Stock", desc: "Stock journals, waste and supplier POs" },
  { key: "DELIVERY", label: "Delivery & Fleet", desc: "Driver assignment, zones and rider app" },
  { key: "TEAM", label: "Staff & HR", desc: "Shift schedules, attendance, payroll and roles" },
  { key: "ACCOUNTING", label: "Accounting", desc: "Cash closings, expenses and bank logs" },
  { key: "REPORTS", label: "Analytics & Reports", desc: "Sales, taxes, items and audit reporting" },
  { key: "MARKETING", label: "Marketing & Loyalty", desc: "Coupons, promotions and loyalty points" },
  { key: "OPERATIONS", label: "Operations & Assets", desc: "Equipment, checklists and documents" },
  { key: "ATTENDANCE", label: "Staff Clock In/Out", desc: "Staff attendance timecard logging" },
  { key: "SETTINGS", label: "Restaurant Settings", desc: "Branch settings, printers and taxes" },
  { key: "VERIFACTU", label: "Spain VERI*FACTU", desc: "Spanish anti-fraud compliance registry" },
  { key: "INTEGRATIONS", label: "Integration APIs", desc: "Website orders and webhook delivery" },
];

export default function SuperAdminLicensesPage() {
  const queryClient = useQueryClient();
  const [selectedRestaurant, setSelectedRestaurant] =
    useState<SuperAdminRestaurantSummary | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  // Edit form state
  const [formStatus, setFormStatus] = useState<LicenseStatus>("ACTIVE");
  const [formValidUntil, setFormValidUntil] = useState<string>("");
  const [formGraceDays, setFormGraceDays] = useState<number>(3);
  const [formMaxBranches, setFormMaxBranches] = useState<number>(1);
  const [formMaxUsers, setFormMaxUsers] = useState<number>(10);
  const [formEnabledModules, setFormEnabledModules] = useState<ModuleKey[]>([]);
  const [formNotes, setFormNotes] = useState<string>("");

  const { data: restaurants, isLoading, error } = useQuery<SuperAdminRestaurantSummary[]>({
    queryKey: ["superadmin", "restaurants"],
    queryFn: () => api.get<SuperAdminRestaurantSummary[]>("/superadmin/restaurants"),
  });

  const updateMutation = useMutation({
    mutationFn: async (payload: { id: string; dto: UpdateLicenseDto }) => {
      return api.patch(`/superadmin/restaurants/${payload.id}/license`, payload.dto);
    },
    onSuccess: () => {
      toast.success("License updated successfully");
      queryClient.invalidateQueries({ queryKey: ["superadmin", "restaurants"] });
      setEditDialogOpen(false);
    },
    onError: (err: unknown) => {
      toast.error(err instanceof ApiError ? err.message : "Failed to update license");
    },
  });

  const openEditModal = (r: SuperAdminRestaurantSummary) => {
    setSelectedRestaurant(r);
    const lic = r.license;
    setFormStatus((lic?.status as LicenseStatus) ?? "ACTIVE");
    const until = lic?.validUntil
      ? new Date(lic.validUntil).toISOString().slice(0, 10)
      : new Date(Date.now() + 365 * 86400000).toISOString().slice(0, 10);
    setFormValidUntil(until);
    setFormGraceDays(lic?.gracePeriodDays ?? 3);
    setFormMaxBranches(lic?.maxBranches ?? 1);
    setFormMaxUsers(lic?.maxUsers ?? 10);
    setFormEnabledModules(
      lic?.enabledModules ?? ["POS", "ORDERS", "TABLES", "MENU", "CUSTOMERS", "SETTINGS"],
    );
    setFormNotes(lic?.notes ?? "");
    setEditDialogOpen(true);
  };

  const toggleModule = (modKey: ModuleKey) => {
    setFormEnabledModules((prev) =>
      prev.includes(modKey) ? prev.filter((k) => k !== modKey) : [...prev, modKey],
    );
  };

  const handleSave = () => {
    if (!selectedRestaurant) return;
    const dto: UpdateLicenseDto = {
      status: formStatus,
      validUntil: new Date(formValidUntil).toISOString(),
      gracePeriodDays: formGraceDays,
      maxBranches: formMaxBranches,
      maxUsers: formMaxUsers,
      enabledModules: formEnabledModules,
      notes: formNotes,
    };
    updateMutation.mutate({ id: selectedRestaurant.id, dto });
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <ShieldAlert className="h-6 w-6 text-primary" />
            Superadmin License Management
          </h1>
          <p className="text-sm text-muted-foreground">
            Manage restaurant subscriptions, license validity, and selectively toggle modules for each tenant.
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-16 w-full rounded-xl" />
          <Skeleton className="h-16 w-full rounded-xl" />
          <Skeleton className="h-16 w-full rounded-xl" />
        </div>
      ) : error ? (
        <Card className="p-6 text-center text-red-500">
          Failed to load restaurants: {(error as any)?.message ?? "Unauthorized"}
        </Card>
      ) : !restaurants || restaurants.length === 0 ? (
        <Card className="p-8 text-center text-muted-foreground">
          No restaurants registered on this system.
        </Card>
      ) : (
        <div className="grid gap-4">
          {restaurants.map((r) => {
            const lic = r.license;
            const isSuspended = lic?.status === "SUSPENDED";
            const isExpired =
              lic?.validUntil && new Date(lic.validUntil).getTime() < Date.now();
            const statusColor = isSuspended
              ? "bg-red-500/10 text-red-600 border-red-200"
              : isExpired
              ? "bg-amber-500/10 text-amber-600 border-amber-200"
              : "bg-emerald-500/10 text-emerald-600 border-emerald-200";

            return (
              <Card key={r.id} className="p-5 transition hover:shadow-sm">
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-base">{r.name}</span>
                      <Badge variant="outline" className={statusColor}>
                        {isSuspended ? (
                          <XCircle className="mr-1 h-3.5 w-3.5" />
                        ) : isExpired ? (
                          <AlertTriangle className="mr-1 h-3.5 w-3.5" />
                        ) : (
                          <CheckCircle2 className="mr-1 h-3.5 w-3.5" />
                        )}
                        {lic?.status ?? "NO_LICENSE"}
                      </Badge>
                    </div>
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Users className="h-3.5 w-3.5" /> Owner: {r.ownerEmail || r.ownerName || "N/A"}
                      </span>
                      <span className="flex items-center gap-1">
                        <Building2 className="h-3.5 w-3.5" /> {r.branchCount} Branch(es) / {r.userCount} User(s)
                      </span>
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3.5 w-3.5" />
                        Expires: {lic?.validUntil ? new Date(lic.validUntil).toLocaleDateString() : "Never"}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1 pt-1.5">
                      {(lic?.enabledModules ?? []).map((mod) => (
                        <span
                          key={mod}
                          className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground"
                        >
                          {mod}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openEditModal(r)}
                      className="gap-2 shrink-0"
                    >
                      <SlidersHorizontal className="h-4 w-4" />
                      Manage License & Modules
                    </Button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* License & Module Configuration Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <SlidersHorizontal className="h-5 w-5 text-primary" />
              Manage License — {selectedRestaurant?.name}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-6 py-2">
            {/* Status & Validity */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-muted-foreground">License Status</label>
                <select
                  value={formStatus}
                  onChange={(e) => setFormStatus(e.target.value as LicenseStatus)}
                  className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="EXPIRED">EXPIRED</option>
                  <option value="SUSPENDED">SUSPENDED</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-muted-foreground">Valid Until (Expiry)</label>
                <Input
                  type="date"
                  value={formValidUntil}
                  onChange={(e) => setFormValidUntil(e.target.value)}
                  className="mt-1"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-muted-foreground">Max Allowed Branches</label>
                <Input
                  type="number"
                  min={1}
                  max={500}
                  value={formMaxBranches}
                  onChange={(e) => setFormMaxBranches(Number(e.target.value))}
                  className="mt-1"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-muted-foreground">Max Staff Seats</label>
                <Input
                  type="number"
                  min={1}
                  max={5000}
                  value={formMaxUsers}
                  onChange={(e) => setFormMaxUsers(Number(e.target.value))}
                  className="mt-1"
                />
              </div>
            </div>

            {/* Modules / Features Switch Grid */}
            <div className="space-y-3">
              <div className="flex items-center justify-between border-b pb-2">
                <span className="font-semibold text-sm">Feature & Module Entitlements</span>
                <span className="text-xs text-muted-foreground">
                  {formEnabledModules.length} of {ALL_MODULES.length} enabled
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[300px] overflow-y-auto pr-1">
                {ALL_MODULES.map((mod) => {
                  const isChecked = formEnabledModules.includes(mod.key);
                  return (
                    <div
                      key={mod.key}
                      onClick={() => toggleModule(mod.key)}
                      className={`flex items-start justify-between p-3 rounded-lg border transition cursor-pointer ${
                        isChecked
                          ? "border-primary/50 bg-primary/5"
                          : "border-border bg-card opacity-75 hover:opacity-100"
                      }`}
                    >
                      <div className="space-y-0.5 pr-2">
                        <div className="text-xs font-semibold">{mod.label}</div>
                        <div className="text-[11px] text-muted-foreground leading-tight">
                          {mod.desc}
                        </div>
                      </div>
                      <Switch
                        checked={isChecked}
                        onCheckedChange={() => toggleModule(mod.key)}
                      />
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Internal Notes */}
            <div>
              <label className="text-xs font-semibold text-muted-foreground">Admin Notes</label>
              <Input
                placeholder="Optional notes or subscription remarks..."
                value={formNotes}
                onChange={(e) => setFormNotes(e.target.value)}
                className="mt-1"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="ghost" onClick={() => setEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={updateMutation.isPending}>
              {updateMutation.isPending ? "Saving…" : "Save Changes"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
