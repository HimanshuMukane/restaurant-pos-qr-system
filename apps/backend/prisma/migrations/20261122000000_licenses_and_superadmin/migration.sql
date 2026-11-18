-- AlterTable
ALTER TABLE "users" ADD COLUMN "isSuperAdmin" BOOLEAN NOT NULL DEFAULT false;

-- CreateEnum
CREATE TYPE "LicenseStatus" AS ENUM ('ACTIVE', 'EXPIRED', 'SUSPENDED');

-- CreateEnum
CREATE TYPE "ModuleKey" AS ENUM (
  'POS',
  'ORDERS',
  'TABLES',
  'RESERVATIONS',
  'MENU',
  'KDS',
  'CUSTOMERS',
  'INVENTORY',
  'DELIVERY',
  'TEAM',
  'ACCOUNTING',
  'REPORTS',
  'MARKETING',
  'OPERATIONS',
  'ATTENDANCE',
  'SETTINGS',
  'VERIFACTU',
  'INTEGRATIONS'
);

-- CreateTable
CREATE TABLE "licenses" (
    "id" TEXT NOT NULL,
    "restaurantId" TEXT NOT NULL,
    "status" "LicenseStatus" NOT NULL DEFAULT 'ACTIVE',
    "validFrom" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "validUntil" TIMESTAMP(3) NOT NULL,
    "gracePeriodDays" INTEGER NOT NULL DEFAULT 3,
    "maxBranches" INTEGER NOT NULL DEFAULT 1,
    "maxUsers" INTEGER NOT NULL DEFAULT 10,
    "enabledModules" "ModuleKey"[] DEFAULT ARRAY['POS'::"ModuleKey", 'ORDERS'::"ModuleKey", 'TABLES'::"ModuleKey", 'MENU'::"ModuleKey", 'CUSTOMERS'::"ModuleKey", 'SETTINGS'::"ModuleKey"],
    "notes" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "licenses_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "licenses_restaurantId_key" ON "licenses"("restaurantId");

-- AddForeignKey
ALTER TABLE "licenses" ADD CONSTRAINT "licenses_restaurantId_fkey" FOREIGN KEY ("restaurantId") REFERENCES "restaurants"("id") ON DELETE CASCADE ON UPDATE CASCADE;
