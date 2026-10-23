"""ensanchar porcentaje_grasa a numeric(5,2)

Revision ID: 9579bae4a653
Revises: 444873b25785
Create Date: 2026-09-11 00:00:00.000000

RN-04 permite 0 a 100 inclusive, pero la columna era NUMERIC(4,2) (máx. 99.99)
y no podía guardar un 100.00 exacto. Se ensancha a NUMERIC(5,2), igual que el
resto de las columnas de medidas, para que el rango real de negocio quepa en
la base. Ver docs/api/api_02_mediciones.md (Limitaciones).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9579bae4a653'
down_revision: Union[str, Sequence[str], None] = '444873b25785'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'mediciones',
        'porcentaje_grasa',
        existing_type=sa.Numeric(precision=4, scale=2),
        type_=sa.Numeric(precision=5, scale=2),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'mediciones',
        'porcentaje_grasa',
        existing_type=sa.Numeric(precision=5, scale=2),
        type_=sa.Numeric(precision=4, scale=2),
        existing_nullable=True,
    )
