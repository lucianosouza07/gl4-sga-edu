import React from "react";

const Rodape: React.FC = () => {
  const ano = new Date().getFullYear();
  return (
    <footer className="rodape" role="contentinfo">
      <div className="container">
        <div className="rodape-conteudo">
          <span>© {ano} SGA-Edu — Sistema de Gestão Acadêmica</span>
          <span>GL4-30 / GL4-34 · Módulo de Professores</span>
        </div>
      </div>
    </footer>
  );
};

export default Rodape;
