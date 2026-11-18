import {
  CanActivate,
  ExecutionContext,
  ForbiddenException,
  Injectable,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { PrismaService } from '../../prisma/prisma.service';
import type { AuthenticatedRequest } from '../types/authenticated-request';
import { REQUIRED_MODULE_KEY } from '../decorators/require-module.decorator';
import { ModuleKey } from '@nodedr-restaurant/types';

@Injectable()
export class LicenseAndModuleGuard implements CanActivate {
  constructor(
    private readonly reflector: Reflector,
    private readonly prisma: PrismaService,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const requiredModule = this.reflector.getAllAndOverride<ModuleKey | undefined>(
      REQUIRED_MODULE_KEY,
      [context.getHandler(), context.getClass()],
    );

    const request = context.switchToHttp().getRequest<AuthenticatedRequest>();
    const user = request.user;
    if (!user) return true; // Let authentication guard handle missing user

    // SuperAdmin bypasses tenant feature/license restrictions
    if (user.isSuperAdmin) return true;

    // Fetch or check the restaurant license
    const license = await this.prisma.license.findUnique({
      where: { restaurantId: user.restaurantId },
    });

    // If no license has been configured yet, allow default access (or grace setup)
    if (!license) {
      return true;
    }

    // Check status
    if (license.status === 'SUSPENDED') {
      throw new ForbiddenException({
        code: 'LICENSE_SUSPENDED',
        message: 'Your restaurant license has been suspended. Please contact administrator.',
      });
    }

    const now = new Date();
    const expiryWithGrace = new Date(license.validUntil);
    expiryWithGrace.setDate(expiryWithGrace.getDate() + (license.gracePeriodDays || 0));

    if (now > expiryWithGrace) {
      throw new ForbiddenException({
        code: 'LICENSE_EXPIRED',
        message: 'Your restaurant license has expired. Please renew to continue.',
      });
    }

    // Check module entitlement if the endpoint requires a module
    if (requiredModule) {
      const isAllowed = license.enabledModules.includes(requiredModule as any);
      if (!isAllowed) {
        throw new ForbiddenException({
          code: 'MODULE_NOT_LICENSED',
          message: `The ${requiredModule} module is not enabled for your restaurant license.`,
        });
      }
    }

    return true;
  }
}
