import { dashboardAPI } from '../../../utils/api';

export async function fetchDashboardData() {
  const response = await dashboardAPI.get();
  return response.data;
}
