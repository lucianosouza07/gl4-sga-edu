from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.database.session import get_db
from app.models.usuario import PerfilUsuario, Usuario
from app.schemas.dashboard import DashboardResponse, PeriodoDashboard
from app.services.dashboard_service import DashboardService


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardResponse, summary="Consultar dashboard institucional")
def obter_dashboard(
    periodo: PeriodoDashboard = Query("ano", description="3 meses, 6 meses ou ano atual, incluindo o mês em andamento"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([PerfilUsuario.ADMIN, PerfilUsuario.SECRETARIA])),
) -> DashboardResponse:
    return DashboardService(db).obter_dashboard(periodo)
