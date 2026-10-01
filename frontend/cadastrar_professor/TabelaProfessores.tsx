import React from "react";
import type { Professor } from "../types/professor";

interface Props {
  professores: Professor[];
  onEditar: (prof: Professor) => void;
  onExcluir: (prof: Professor) => void;
  carregando?: boolean;
}

const TabelaProfessores: React.FC<Props> = ({ professores, onEditar, onExcluir, carregando }) => {
  if (carregando) {
    return (
      <div className="sem-dados" role="status" aria-live="polite">
        ⏳ Carregando professores…
      </div>
    );
  }

  if (professores.length === 0) {
    return (
      <div className="sem-dados" role="status">
        📋 Nenhum professor cadastrado ainda.
      </div>
    );
  }

  return (
    <div className="tabela-wrapper">
      <table className="tabela-professores" aria-label="Lista de professores cadastrados">
        <caption className="sr-only">Tabela de professores cadastrados no sistema</caption>
        <thead>
          <tr>
            <th scope="col">#</th>
            <th scope="col">Nome</th>
            <th scope="col">E-mail</th>
            <th scope="col">CPF</th>
            <th scope="col">Departamento</th>
            <th scope="col">Titulação</th>
            <th scope="col">Ações</th>
          </tr>
        </thead>
        <tbody>
          {professores.map((prof) => (
            <tr key={prof.id}>
              <td>{prof.id}</td>
              <td>{prof.nome}</td>
              <td>{prof.email}</td>
              <td>
                {prof.cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4")}
              </td>
              <td>{prof.departamento}</td>
              <td>
                <span className="badge-titulacao">{prof.titulacao}</span>
              </td>
              <td>
                <div className="tabela-acoes">
                  <button
                    className="btn btn-secundario btn-sm"
                    onClick={() => onEditar(prof)}
                    aria-label={`Editar professor ${prof.nome}`}
                  >
                    ✏️ Editar
                  </button>
                  <button
                    className="btn btn-perigo btn-sm"
                    onClick={() => onExcluir(prof)}
                    aria-label={`Excluir professor ${prof.nome}`}
                  >
                    🗑️ Excluir
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TabelaProfessores;
