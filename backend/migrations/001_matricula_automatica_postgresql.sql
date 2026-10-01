-- Apenas para bancos PostgreSQL já existentes. Novos bancos usam init_db().
BEGIN;

ALTER TABLE alunos ALTER COLUMN matricula TYPE VARCHAR;

CREATE TABLE IF NOT EXISTS sequencias_matricula (
    ano INTEGER NOT NULL,
    semestre INTEGER NOT NULL,
    ultimo_numero BIGINT NOT NULL,
    PRIMARY KEY (ano, semestre)
);

COMMIT;
