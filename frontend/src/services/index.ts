import { ILifecycleService } from './api';
import { MockLifecycleService } from './mockLifecycleService';

// Singleton instance of the lifecycle service
export const lifecycleService: ILifecycleService = new MockLifecycleService();

export * from './api';
export * from './types';
export * from './dateUtils';
export * from './digestService';
