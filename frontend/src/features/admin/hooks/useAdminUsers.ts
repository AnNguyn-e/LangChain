import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminService, UpdateRoleData, UpdateStatusData } from '../services/adminService';
import { User } from '../../auth/models/user';

export const useAdminUsers = () => {
  const queryClient = useQueryClient();

  const usersQuery = useQuery<User[], Error>({
    queryKey: ['admin_users'],
    queryFn: adminService.getUsers,
  });

  const updateRoleMutation = useMutation({
    mutationFn: ({ userId, data }: { userId: number; data: UpdateRoleData }) => 
      adminService.updateUserRole(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin_users'] });
    },
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ userId, data }: { userId: number; data: UpdateStatusData }) => 
      adminService.updateUserStatus(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin_users'] });
    },
  });

  return {
    users: usersQuery.data,
    isLoading: usersQuery.isLoading,
    error: usersQuery.error,
    updateRole: updateRoleMutation.mutateAsync,
    updateStatus: updateStatusMutation.mutateAsync,
    isUpdating: updateRoleMutation.isPending || updateStatusMutation.isPending,
  };
};
