const API = "http://127.0.0.1:8000/api";

const form = document.getElementById("form-professor");
const mensagem = document.getElementById("mensagem");
const btnSalvar = document.getElementById("btn-salvar");
const btnCancelar = document.getElementById("btn-cancelar");
const tituloForm = document.getElementById("titulo-form");
const tabela = document.getElementById("tabela-professores");
const vazio = document.getElementById("vazio");

let professores = [];
let editandoId = null;

// ===== API =====
async function api(rota, opcoes = {}) {
  const resp = await fetch(`${API}${rota}`, {
    ...opcoes,
    headers: { "Content-Type": "application/json" },
  });
  const corpo = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const erro = new Error("Erro na API");
    erro.status = resp.status;
    erro.corpo = corpo;
    throw erro;
  }
  return corpo;
}

// ===== Máscaras =====
function mascararCpf(v) {
  const d = v.replace(/\D/g, "").slice(0, 11);
  return d
    .replace(/^(\d{3})(\d)/, "$1.$2")
    .replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
    .replace(/\.(\d{3})(\d)/, ".$1-$2");
}

function mascararTelefone(v) {
  const d = v.replace(/\D/g, "").slice(0, 11);
  if (d.length <= 2) return d ? `(${d}` : "";
  if (d.length <= 6) return `(${d.slice(0, 2)}) ${d.slice(2)}`;
  if (d.length <= 10)
    return `(${d.slice(0, 2)}) ${d.slice(2, 6)}-${d.slice(6)}`;
  return `(${d.slice(0, 2)}) ${d.slice(2, 7)}-${d.slice(7)}`;
}

form.cpf.addEventListener("input", (e) => {
  e.target.value = mascararCpf(e.target.value);
});
form.telefone.addEventListener("input", (e) => {
  e.target.value = mascararTelefone(e.target.value);
});

// ===== Validação =====
function limparErros() {
  document
    .querySelectorAll(".campo")
    .forEach((c) => c.classList.remove("invalido"));
  document.querySelectorAll("[data-erro]").forEach((s) => (s.textContent = ""));
}

function mostrarErro(campo, texto) {
  const alvo = document.querySelector(`[data-erro="${campo}"]`);
  if (!alvo) return;
  alvo.textContent = texto;
  alvo.closest(".campo").classList.add("invalido");
}

function validar(d) {
  const erros = {};
  if (d.nome.trim().length < 3) erros.nome = "Informe o nome completo.";
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(d.email.trim()))
    erros.email = "Informe um e-mail válido.";
  if (d.cpf.replace(/\D/g, "").length !== 11)
    erros.cpf = "O CPF deve ter 11 dígitos.";
  if (d.telefone && d.telefone.replace(/\D/g, "").length < 10)
    erros.telefone = "Telefone incompleto.";
  if (!d.titulacao) erros.titulacao = "Selecione a titulação.";
  if (d.departamento.trim().length < 2)
    erros.departamento = "Informe o departamento.";
  return erros;
}

function mostrarMensagem(texto, tipo) {
  mensagem.textContent = texto;
  mensagem.className = `mensagem ${tipo || ""}`;
}

// ===== Lista =====
function escapar(t) {
  const el = document.createElement("div");
  el.textContent = t;
  return el.innerHTML;
}

function desenharTabela() {
  vazio.hidden = professores.length > 0;
  tabela.innerHTML = professores
    .map(
      (p) => `
    <tr>
      <td>${escapar(p.nome)}<span class="email">${escapar(p.email)}</span></td>
      <td>${escapar(p.departamento)}</td>
      <td>${escapar(p.titulacao)}</td>
      <td>
        <button class="acao-link" data-editar="${p.id}">Editar</button>
        <button class="acao-link perigo" data-excluir="${p.id}">Excluir</button>
      </td>
    </tr>
  `,
    )
    .join("");
}

async function carregarProfessores() {
  professores = await api("/professores");
  desenharTabela();
}

// ===== Formulário =====
function dadosDoForm() {
  return {
    nome: form.nome.value.trim(),
    email: form.email.value.trim(),
    cpf: form.cpf.value,
    telefone: form.telefone.value.trim() || null,
    departamento: form.departamento.value.trim(),
    titulacao: form.titulacao.value,
  };
}

function sairDaEdicao() {
  editandoId = null;
  form.reset();
  limparErros();
  tituloForm.textContent = "Novo professor";
  btnSalvar.textContent = "Cadastrar professor";
  btnCancelar.hidden = true;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  limparErros();
  mostrarMensagem("");

  const dados = dadosDoForm();
  const erros = validar({ ...dados, telefone: dados.telefone || "" });
  if (Object.keys(erros).length) {
    Object.entries(erros).forEach(([campo, texto]) =>
      mostrarErro(campo, texto),
    );
    return;
  }

  btnSalvar.disabled = true;
  try {
    if (editandoId) {
      await api(`/professores/${editandoId}`, {
        method: "PUT",
        body: JSON.stringify(dados),
      });
      mostrarMensagem("Professor atualizado.", "ok");
    } else {
      await api("/professores", {
        method: "POST",
        body: JSON.stringify(dados),
      });
      mostrarMensagem("Professor cadastrado.", "ok");
    }
    sairDaEdicao();
    await carregarProfessores();
  } catch (err) {
    if (err.status === 409) {
      const msg = err.corpo.detail || "Professor já cadastrado.";
      mostrarMensagem(msg, "falha");
      mostrarErro(msg.includes("CPF") ? "cpf" : "email", msg);
    } else if (err.status === 422) {
      mostrarMensagem("Confira os campos e tente de novo.", "falha");
    } else {
      mostrarMensagem(
        "Não foi possível salvar. Verifique se o servidor está rodando.",
        "falha",
      );
    }
  } finally {
    btnSalvar.disabled = false;
  }
});

btnCancelar.addEventListener("click", () => {
  sairDaEdicao();
  mostrarMensagem("");
});

tabela.addEventListener("click", async (e) => {
  const editar = e.target.closest("[data-editar]");
  const excluir = e.target.closest("[data-excluir]");

  if (editar) {
    const p = professores.find((x) => x.id === Number(editar.dataset.editar));
    if (!p) return;
    editandoId = p.id;
    form.nome.value = p.nome;
    form.email.value = p.email;
    form.cpf.value = mascararCpf(p.cpf);
    form.telefone.value = p.telefone || "";
    form.departamento.value = p.departamento;
    form.titulacao.value = p.titulacao;
    tituloForm.textContent = "Editar professor";
    btnSalvar.textContent = "Salvar alterações";
    btnCancelar.hidden = false;
    mostrarMensagem("");
    form.nome.focus();
  }

  if (excluir) {
    const p = professores.find((x) => x.id === Number(excluir.dataset.excluir));
    if (!p || !confirm(`Excluir o professor ${p.nome}?`)) return;
    try {
      await api(`/professores/${p.id}`, { method: "DELETE" });
      if (editandoId === p.id) sairDaEdicao();
      mostrarMensagem("Professor excluído.", "ok");
      await carregarProfessores();
    } catch {
      mostrarMensagem("Não foi possível excluir.", "falha");
    }
  }
});

carregarProfessores().catch(() => {
  mostrarMensagem(
    "Não foi possível conectar ao servidor. Verifique se o backend está rodando.",
    "falha",
  );
});
