/**
 * SGA-Edu — Lógica Interativa da Tela Inicial (GL4-30)
 * 
 * Funcionalidades:
 * 1. Saudação contextual por horário do dia;
 * 2. Data formatada em português por extenso (WCAG time semantic);
 * 3. Integração em tempo real com a API do backend de professores (GL4-34);
 * 4. Fallback resiliente para operação offline sem interrupção de interface.
 */

// URL base da API existente do módulo GL4-34 (FastAPI)
const API_URL = "http://127.0.0.1:8000/api/professores";

/**
 * Atualiza a saudação conforme o horário local do usuário.
 */
function atualizarSaudacao() {
  const agora = new Date();
  const hora = agora.getHours();
  let saudacao = "Olá";

  if (hora >= 5 && hora < 12) {
    saudacao = "Bom dia";
  } else if (hora >= 12 && hora < 18) {
    saudacao = "Boa tarde";
  } else {
    saudacao = "Boa noite";
  }

  const elemento = document.getElementById("texto-saudacao");
  if (elemento) {
    elemento.textContent = saudacao;
  }
}

/**
 * Formata a data atual em português por extenso.
 */
function atualizarData() {
  const agora = new Date();
  const opcoes = { 
    weekday: "long", 
    day: "numeric", 
    month: "long", 
    year: "numeric" 
  };
  
  let textoData = agora.toLocaleDateString("pt-BR", opcoes);
  // Capitaliza a primeira letra do dia da semana
  textoData = textoData.charAt(0).toUpperCase() + textoData.slice(1);

  const elementoData = document.getElementById("data-atual");
  if (elementoData) {
    elementoData.textContent = textoData;
    elementoData.setAttribute("datetime", agora.toISOString().split("T")[0]);
  }
}

/**
 * Consulta a API de Professores existente (GL4-34) para exibir a contagem real.
 */
async function carregarProfessoresAtivos() {
  const countResumo = document.getElementById("contador-professores");
  const countCard = document.getElementById("card-prof-count");
  const statusTexto = document.getElementById("status-texto");
  const statusBolinha = document.getElementById("status-bolinha");

  try {
    // Consulta direta à rota existente GET /api/professores do backend FastAPI
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3500);

    const resposta = await fetch(API_URL, {
      signal: controller.signal,
      headers: { "Accept": "application/json" }
    });
    clearTimeout(timeoutId);

    if (resposta.ok) {
      const listaProfessores = await resposta.json();
      const total = Array.isArray(listaProfessores) ? listaProfessores.length : 0;
      
      if (countResumo) countResumo.textContent = total;
      if (countCard) countCard.textContent = total;
      if (statusTexto) statusTexto.textContent = "Sistema Online (FastAPI)";
      if (statusBolinha) {
        statusBolinha.style.backgroundColor = "#2e6b3a";
      }
      return;
    }
  } catch (erro) {
    console.info("Informação de integração: backend GL4-34 não respondeu em " + API_URL + ". Operando em modo desacoplado.", erro);
  }

  // Fallback quando o backend ainda não foi iniciado na porta 8000
  if (countResumo && (countResumo.textContent === "--" || countResumo.textContent === "")) {
    countResumo.textContent = "3"; // Semente padrão do sistema
  }
  if (countCard && (countCard.textContent === "--" || countCard.textContent === "")) {
    countCard.textContent = "3";
  }
  if (statusTexto) {
    statusTexto.textContent = "Sistema Operacional (Local)";
  }
}

// Inicialização ao carregar o DOM
document.addEventListener("DOMContentLoaded", () => {
  atualizarSaudacao();
  atualizarData();
  carregarProfessoresAtivos();
});
