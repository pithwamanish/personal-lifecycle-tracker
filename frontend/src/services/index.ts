import { ILifecycleService } from './api';
import { BackendLifecycleService } from './backendLifecycleService';

// Singleton instance of the lifecycle service using the real backend client
export const lifecycleService: ILifecycleService = new BackendLifecycleService();

export * from './api';
export * from './backendLifecycleService';
export * from './mockLifecycleService';
export * from './types';
export * from './dateUtils';
export * from './digestService';
