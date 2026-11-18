import { Module } from '@nestjs/common';
import { SuperAdminController } from './superadmin.controller';
import { PrismaModule } from '../../prisma/prisma.module';

@Module({
  imports: [PrismaModule],
  controllers: [SuperAdminController],
  exports: [],
})
export class SuperAdminModule {}
