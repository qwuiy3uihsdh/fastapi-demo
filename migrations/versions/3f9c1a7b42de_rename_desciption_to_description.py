"""rename desciption to description

Revision ID: 3f9c1a7b42de
Revises: 082e9702a9c8
Create Date: 2026-09-17

修正 permissions / roles 两表中的列名拼写错误：desciption -> description。
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '3f9c1a7b42de'
down_revision: Union[str, Sequence[str], None] = '082e9702a9c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('permissions', 'desciption', new_column_name='description')
    op.alter_column('roles', 'desciption', new_column_name='description')


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('permissions', 'description', new_column_name='desciption')
    op.alter_column('roles', 'description', new_column_name='desciption')
