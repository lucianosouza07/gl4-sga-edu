import React, { useState, useEffect } from "react";
import type { Professor, ProfessorEntrada } from "../types/professor";

interface Props {
  professor?: Professor | null;
  onSalvar: (dados: ProfessorEntrada) => Promise<void>;
  onCancelar: () => void;
  carregando?: boolean;
  erro?: string | null;
}

const TITULACOES = ["Graduação", "Especialização", "Mestrado", "Doutorado"] as const;

const vazio: ProfessorEntrada = {
  nome: "", email: "", cpf: "", telefone: "", departamento: "", titulacao: "Graduação",
};

// Máscara CPF: 000.000.000-00
function mascaraCpf(valor: string): string {
  return valor
    .replace(/\D/g, "")
    .slice(0, 11)
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
}

// Máscara telefone: (00) 00000-0000
function mascaraTelefone(valor: string): string {
  return valor
    .replace(/\D/g, "")
    .slice(0, 11)
    .replace(/(\d{2})(\d)/, "($1) $2")
    .replace(/(\d{5})(\d)/, "$1-$2");
}

const FormularioProfessor: React.FC<Props> = ({
  professor, onSalvar, onCancelar, carregando = false, erro = null,
}) => {
  const [form, setForm] = useState<ProfessorEntrada>(vazio);
  const [erros, setErros] = useState<Partial<Record<keyof ProfessorEntrada, string>>>({});

  useEffect(() => {
    if (professor) {
      setForm({
        nome: professor.nome,
        email: professor.email,
        cpf: mascaraCpf(professor.cpf),
        telefone: professor.telefone ? mascaraTelefone(professor.telefone) : "",
        departamento: professor.departamento,
        titulacao: professor.titulacao,
      });
    } else {
      setForm(vazio);
    }
    setErros({});
  }, [professor]);

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    const { name, value } = e.target;
    let v = value;
    if (name === "cpf") v = mascaraCpf(value);
    if (name === "telefone") v = mascaraTelefone(value);
    setForm(prev => ({ ...prev, [name]: v }));
    setErros(prev => ({ ...prev, [name]: undefined }));
  }

  function validar(): boolean {
    const novosErros: Partial<Record<keyof ProfessorEntrada, string>> = {};
    if (!form.nome.trim() || form.nome.trim().length < 3)
      novosErros.nome = "Nome deve ter ao menos 3 caracteres.";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email))
      novosErros.email = "E-mail inválido.";
    if (form.cpf.replace(/\D/g, "").length !== 11)
      novosErros.cpf = "CPF deve ter 11 dígitos.";
    if (!form.departamento.trim() || form.departamento.trim().length < 2)
      novosErros.departamento = "Departamento deve ter ao menos 2 caracteres.";
    if (!TITULACOES.includes(form.titulacao as typeof TITULACOES[number]))
      novosErros.titulacao = "Titulação inválida.";
    setErros(novosErros);
    return Object.keys(novosErros).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validar()) return;
    await onSalvar({
      ...form,
      cpf: form.cpf.replace(/\D/g, ""),
      telefone: (form.telefone ?? "").replace(/\D/g, "") || "",
    });
  }

  return (
    <div className="form-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="form-titulo">
      <div className="form-modal">
        <h2 id="form-titulo">{professor ? "Editar Professor" : "Novo Professor"}</h2>

        {erro && <div className="alerta alerta-erro" role="alert">⚠️ {erro}</div>}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-grade">
            {/* Nome */}
            <div className="form-grupo col-full">
              <label htmlFor="nome">Nome completo *</label>
              <input
                id="nome" name="nome" type="text" autoComplete="name"
                value={form.nome} onChange={handleChange}
                aria-required="true" aria-invalid={!!erros.nome}
                aria-describedby={erros.nome ? "erro-nome" : undefined}
              />
              {erros.nome && <span id="erro-nome" role="alert" style={{ color: "var(--erro)", fontSize: ".78rem" }}>{erros.nome}</span>}
            </div>

            {/* E-mail */}
            <div className="form-grupo col-full">
              <label htmlFor="email">E-mail *</label>
              <input
                id="email" name="email" type="email" autoComplete="email"
                value={form.email} onChange={handleChange}
                aria-required="true" aria-invalid={!!erros.email}
                aria-describedby={erros.email ? "erro-email" : undefined}
              />
              {erros.email && <span id="erro-email" role="alert" style={{ color: "var(--erro)", fontSize: ".78rem" }}>{erros.email}</span>}
            </div>

            {/* CPF */}
            <div className="form-grupo">
              <label htmlFor="cpf">CPF *</label>
              <input
                id="cpf" name="cpf" type="text" inputMode="numeric" autoComplete="off"
                value={form.cpf} onChange={handleChange} placeholder="000.000.000-00"
                aria-required="true" aria-invalid={!!erros.cpf}
                aria-describedby={erros.cpf ? "erro-cpf" : undefined}
              />
              {erros.cpf && <span id="erro-cpf" role="alert" style={{ color: "var(--erro)", fontSize: ".78rem" }}>{erros.cpf}</span>}
            </div>

            {/* Telefone */}
            <div className="form-grupo">
              <label htmlFor="telefone">Telefone</label>
              <input
                id="telefone" name="telefone" type="tel" autoComplete="tel"
                value={form.telefone ?? ""} onChange={handleChange} placeholder="(00) 00000-0000"
              />
            </div>

            {/* Departamento */}
            <div className="form-grupo col-full">
              <label htmlFor="departamento">Departamento *</label>
              <input
                id="departamento" name="departamento" type="text"
                value={form.departamento} onChange={handleChange}
                aria-required="true" aria-invalid={!!erros.departamento}
                aria-describedby={erros.departamento ? "erro-dep" : undefined}
              />
              {erros.departamento && <span id="erro-dep" role="alert" style={{ color: "var(--erro)", fontSize: ".78rem" }}>{erros.departamento}</span>}
            </div>

            {/* Titulação */}
            <div className="form-grupo col-full">
              <label htmlFor="titulacao">Titulação *</label>
              <select
                id="titulacao" name="titulacao"
                value={form.titulacao} onChange={handleChange}
                aria-required="true"
              >
                {TITULACOES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </div>

          <div className="form-acoes">
            <button type="button" className="btn btn-secundario" onClick={onCancelar} disabled={carregando}>
              Cancelar
            </button>
            <button type="submit" className="btn btn-primario" disabled={carregando}>
              {carregando ? "Salvando…" : professor ? "Salvar alterações" : "Cadastrar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default FormularioProfessor;
