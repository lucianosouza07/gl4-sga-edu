from sqlalchemy import Column, Integer

from app.database.session import Base


class SequenciaMatricula(Base):
    """High-water mark for each calendar-year and semester pair."""

    __tablename__ = "sequencias_matricula"

    ano = Column(Integer, primary_key=True)
    semestre = Column(Integer, primary_key=True)
    ultimo_numero = Column(Integer, nullable=False)
