"""merge heads

Revision ID: 512da4a7b0ad
Revises: 20260324_01, 7c619132cb12
Create Date: 2026-03-25 01:44:42.093689

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '512da4a7b0ad'
down_revision: Union[str, Sequence[str], None] = ('20260324_01', '7c619132cb12')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
