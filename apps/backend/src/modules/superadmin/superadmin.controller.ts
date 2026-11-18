import {
  Body,
  Controller,
  Get,
  Param,
  Patch,
  UseGuards,
  ValidationPipe,
} from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';
import { JwtAuthGuard } from '../../common/guards/jwt-auth.guard';
import { SuperAdminGuard } from '../../common/guards/super-admin.guard';
import type {
  UpdateLicenseDto,
  SuperAdminRestaurantSummary,
  LicenseDto,
} from '@nodedr-restaurant/types';

@Controller('v1/superadmin')
@UseGuards(JwtAuthGuard, SuperAdminGuard)
export class SuperAdminController {
  constructor(private readonly prisma: PrismaService) {}

  @Get('restaurants')
  async listRestaurants(): Promise<SuperAdminRestaurantSummary[]> {
    const restaurants = await this.prisma.restaurant.findMany({
      orderBy: { createdAt: 'desc' },
      include: {
        branches: { select: { id: true } },
        users: {
          select: {
            id: true,
            email: true,
            name: true,
            role: { select: { name: true } },
          },
        },
        license: true,
      },
    });

    return restaurants.map((r) => {
      const owner = r.users.find((u) => u.role?.name === 'OWNER') || r.users[0];
      return {
        id: r.id,
        name: r.name,
        createdAt: r.createdAt.toISOString(),
        ownerEmail: owner?.email ?? null,
        ownerName: owner?.name ?? null,
        branchCount: r.branches.length,
        userCount: r.users.length,
        license: r.license
          ? {
              id: r.license.id,
              restaurantId: r.license.restaurantId,
              status: r.license.status as any,
              validFrom: r.license.validFrom.toISOString(),
              validUntil: r.license.validUntil.toISOString(),
              gracePeriodDays: r.license.gracePeriodDays,
              maxBranches: r.license.maxBranches,
              maxUsers: r.license.maxUsers,
              enabledModules: r.license.enabledModules as any,
              notes: r.license.notes,
              createdAt: r.license.createdAt.toISOString(),
              updatedAt: r.license.updatedAt.toISOString(),
            }
          : null,
      };
    });
  }

  @Get('restaurants/:id/license')
  async getRestaurantLicense(
    @Param('id') restaurantId: string,
  ): Promise<LicenseDto | null> {
    const license = await this.prisma.license.findUnique({
      where: { restaurantId },
    });
    if (!license) return null;

    return {
      id: license.id,
      restaurantId: license.restaurantId,
      status: license.status as any,
      validFrom: license.validFrom.toISOString(),
      validUntil: license.validUntil.toISOString(),
      gracePeriodDays: license.gracePeriodDays,
      maxBranches: license.maxBranches,
      maxUsers: license.maxUsers,
      enabledModules: license.enabledModules as any,
      notes: license.notes,
      createdAt: license.createdAt.toISOString(),
      updatedAt: license.updatedAt.toISOString(),
    };
  }

  @Patch('restaurants/:id/license')
  async updateRestaurantLicense(
    @Param('id') restaurantId: string,
    @Body(new ValidationPipe({ transform: true, whitelist: true }))
    dto: UpdateLicenseDto,
  ): Promise<LicenseDto> {
    const now = new Date();
    const oneYearLater = new Date(now);
    oneYearLater.setFullYear(oneYearLater.getFullYear() + 1);

    const data: any = {};
    if (dto.status !== undefined) data.status = dto.status;
    if (dto.validUntil !== undefined) data.validUntil = new Date(dto.validUntil);
    if (dto.gracePeriodDays !== undefined)
      data.gracePeriodDays = dto.gracePeriodDays;
    if (dto.maxBranches !== undefined) data.maxBranches = dto.maxBranches;
    if (dto.maxUsers !== undefined) data.maxUsers = dto.maxUsers;
    if (dto.enabledModules !== undefined)
      data.enabledModules = dto.enabledModules;
    if (dto.notes !== undefined) data.notes = dto.notes;

    const license = await this.prisma.license.upsert({
      where: { restaurantId },
      update: data,
      create: {
        restaurantId,
        validUntil: dto.validUntil ? new Date(dto.validUntil) : oneYearLater,
        status: dto.status ?? 'ACTIVE',
        gracePeriodDays: dto.gracePeriodDays ?? 3,
        maxBranches: dto.maxBranches ?? 1,
        maxUsers: dto.maxUsers ?? 10,
        enabledModules: dto.enabledModules ?? [
          'POS',
          'ORDERS',
          'TABLES',
          'MENU',
          'CUSTOMERS',
          'SETTINGS',
        ],
        notes: dto.notes ?? null,
      },
    });

    return {
      id: license.id,
      restaurantId: license.restaurantId,
      status: license.status as any,
      validFrom: license.validFrom.toISOString(),
      validUntil: license.validUntil.toISOString(),
      gracePeriodDays: license.gracePeriodDays,
      maxBranches: license.maxBranches,
      maxUsers: license.maxUsers,
      enabledModules: license.enabledModules as any,
      notes: license.notes,
      createdAt: license.createdAt.toISOString(),
      updatedAt: license.updatedAt.toISOString(),
    };
  }
}
