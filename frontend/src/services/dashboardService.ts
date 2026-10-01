import { api } from "@/services/api";
import type { Dashboard, PeriodoDashboard } from "@/types/dashboard";

export const dashboardService = {
  async obter(periodo: PeriodoDashboard, signal: AbortSignal): Promise<Dashboard> {
    const response = await api.get<Dashboard>("/dashboard", { params: { periodo }, signal });
    return response.data;
  },
};
