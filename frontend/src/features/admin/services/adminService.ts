import api from '../../../lib/api';
import { UserInfo as User } from '../../auth/models/user';

export interface UpdateRoleData {
  role: 'USER' | 'MANAGER' | 'ADMIN';
}

export interface UpdateStatusData {
  is_active: boolean;
}

export const adminService = {
  getUsers: async (): Promise<User[]> => {
    const response = await api.get('/admin/users');
    return response.data;
  },
  
  updateUserRole: async (userId: number, data: UpdateRoleData): Promise<User> => {
    const response = await api.patch(`/admin/users/${userId}/role`, data);
    return response.data;
  },
  
  updateUserStatus: async (userId: number, data: UpdateStatusData): Promise<User> => {
    const response = await api.patch(`/admin/users/${userId}/status`, data);
    return response.data;
  }
};
