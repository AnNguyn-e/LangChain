export interface DashboardStats {
  total_users: number;
  total_documents: number;
  total_chats: number;
  total_storage_mb: number;
  recent_documents: RecentDocument[];
}

export interface RecentDocument {
  id: number;
  filename: string;
  created_at: string;
  status: string;
}

export interface DashboardResponse {
  success: boolean;
  data: DashboardStats;
}
