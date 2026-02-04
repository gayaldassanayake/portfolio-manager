import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';
import type {
  NotificationSetting,
  NotificationSettingUpdate,
  NotificationWithFD,
} from '../../types';

// Query keys
export const notificationKeys = {
  all: ['notifications'] as const,
  settings: () => [...notificationKeys.all, 'settings'] as const,
  pending: () => [...notificationKeys.all, 'pending'] as const,
};

/**
 * Fetch notification settings
 */
export function useNotificationSettings() {
  return useQuery<NotificationSetting>({
    queryKey: notificationKeys.settings(),
    queryFn: () => api.notifications.getSettings(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Update notification settings
 */
export function useUpdateNotificationSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: NotificationSettingUpdate) => api.notifications.updateSettings(data),
    onSuccess: () => {
      // Invalidate settings query
      queryClient.invalidateQueries({ queryKey: notificationKeys.settings() });
    },
  });
}

/**
 * Fetch pending notifications
 * Auto-refetches every 60 seconds
 */
export function usePendingNotifications() {
  return useQuery<NotificationWithFD[]>({
    queryKey: notificationKeys.pending(),
    queryFn: () => api.notifications.getPending(),
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refetch every 60 seconds
  });
}

/**
 * Generate notifications for upcoming maturities
 */
export function useGenerateNotifications() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => api.notifications.generateNotifications(),
    onSuccess: () => {
      // Invalidate pending notifications to show new ones
      queryClient.invalidateQueries({ queryKey: notificationKeys.pending() });
    },
  });
}

/**
 * Mark a notification as displayed
 */
export function useMarkNotificationDisplayed() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.notifications.markDisplayed(id),
    onSuccess: () => {
      // Invalidate pending notifications
      queryClient.invalidateQueries({ queryKey: notificationKeys.pending() });
    },
  });
}

/**
 * Dismiss multiple notifications
 */
export function useDismissNotifications() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ids: number[]) => api.notifications.dismiss(ids),
    onSuccess: () => {
      // Invalidate pending notifications
      queryClient.invalidateQueries({ queryKey: notificationKeys.pending() });
    },
  });
}
