import api from '../../../lib/api';
import { DashboardResponse } from '../models/stats';

export const dashboardService = {
  getStats: async (): Promise<DashboardResponse> => {
    const response = await api.get('/dashboard/stats');
    return response.data;
  }
};
