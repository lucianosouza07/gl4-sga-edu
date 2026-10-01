import { useState, useEffect, useCallback } from "react";
import { dashboardApi } from "../services/dashboard.api";
import type { Dashboard, PeriodoDashboard } from "../data/dashboard.types";

export function useDashboard(periodoInicial: PeriodoDashboard = "ano") {
  const [periodo, setPeriodo] = useState<PeriodoDashboard>(periodoInicial);
  const [atualizacao, setAtualizacao] = useState(0);
  const [dados, setDados] = useState<Dashboard | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState(false);
  const [ultimaConsulta, setUltimaConsulta] = useState<string | null>(null);
  const [ano, setAno] = useState<number | null>(null);

  const consultar = useCallback((proximoPeriodo: PeriodoDashboard = periodo) => {
    setCarregando(true);
    setErro(false);
    setDados(null);
    setPeriodo(proximoPeriodo);
    setAtualizacao((valor) => valor + 1);
  }, [periodo]);

  useEffect(() => {
    const controller = new AbortController();
    dashboardApi
      .obter(periodo, controller.signal)
      .then((resposta) => {
        if (controller.signal.aborted) return;
        setDados(resposta);
        setUltimaConsulta(resposta.gerado_em);
        setAno(resposta.ano);
      })
      .catch(() => {
        if (!controller.signal.aborted) setErro(true);
      })
      .finally(() => {
        if (!controller.signal.aborted) setCarregando(false);
      });
    return () => controller.abort();
  }, [periodo, atualizacao]);

  return {
    periodo,
    dados,
    carregando,
    erro,
    ultimaConsulta,
    ano,
    consultar,
    setPeriodo,
  };
}
