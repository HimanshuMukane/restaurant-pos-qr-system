import { SetMetadata } from '@nestjs/common';
import { ModuleKey } from '@nodedr-restaurant/types';

export const REQUIRED_MODULE_KEY = 'required_module';
export const RequireModule = (moduleKey: ModuleKey) =>
  SetMetadata(REQUIRED_MODULE_KEY, moduleKey);
