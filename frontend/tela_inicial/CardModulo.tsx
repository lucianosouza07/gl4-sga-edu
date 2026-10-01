import React from "react";

interface Props {
  icone: string;
  nome: string;
  descricao: string;
  status: "ativo" | "em-breve";
  /** Texto exibido no contador opcional (ex: "5 professores cadastrados") */
  contador?: string;
  acoes?: React.ReactNode;
}

const CardModulo: React.FC<Props> = ({ icone, nome, descricao, status, contador, acoes }) => {
  return (
    <article className="card-modulo" aria-label={`Módulo: ${nome}`}>
      <div className="card-modulo-topo">
        <div className="card-icone" aria-hidden="true">{icone}</div>
        <div className="card-info">
          <div className="card-nome">{nome}</div>
          {status === "ativo"
            ? <span className="badge-ativo">✅ Ativo</span>
            : <span className="badge-em-breve">🔒 Em breve</span>
          }
        </div>
      </div>
      <p className="card-descricao">{descricao}</p>
      {contador && <p className="card-contador">{contador}</p>}
      {acoes && <div className="card-acoes">{acoes}</div>}
    </article>
  );
};

export default CardModulo;
