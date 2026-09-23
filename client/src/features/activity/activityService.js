import { activityAPI } from "../../utils/api";

export async function getActivities(limit = 100) {
  const response = await activityAPI.list(limit);
  return response.data;
}

export async function getLoginSessions() {
  const response = await activityAPI.sessions();
  return response.data;
}