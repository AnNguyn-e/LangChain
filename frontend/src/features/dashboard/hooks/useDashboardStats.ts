import { useQuery } from '@tanstack/react-query';
import { dashboardService } from '../services/dashboardService';
import { DashboardStats } from '../models/stats';

export const useDashboardStats = () => {
  return useQuery<DashboardStats, Error>({
    queryKey: ['dashboard_stats'],
    queryFn: async () => {
      const response = await dashboardService.getStats();
      if (!response.success) {
        throw new Error('Failed to fetch dashboard stats');
      }
      return response.data;
    },
    staleTime: 60000, // 1 minute
  });
};
