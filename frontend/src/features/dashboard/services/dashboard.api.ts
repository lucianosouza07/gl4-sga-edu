import { apiClient } from "@/api/client";
import type { Dashboard, PeriodoDashboard } from "../data/dashboard.types";

export const dashboardApi = {
  async obter(periodo: PeriodoDashboard = "ano", signal?: AbortSignal): Promise<Dashboard> {
    const response = await apiClient.get<Dashboard>("/dashboard", {
      params: { periodo },
      signal,
    });
    return response.data;
  },
};
