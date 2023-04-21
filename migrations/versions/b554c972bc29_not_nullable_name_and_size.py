"""not nullable name and size

Revision ID: b554c972bc29
Revises: eb749a277c2e
Create Date: 2023-04-10 08:57:16.993127

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'b554c972bc29'
down_revision = 'eb749a277c2e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('inventory', schema=None) as batch_op:
        batch_op.alter_column('name',
               existing_type=mysql.VARCHAR(length=256),
               nullable=False)
        batch_op.alter_column('size',
               existing_type=mysql.VARCHAR(length=16),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('inventory', schema=None) as batch_op:
        batch_op.alter_column('size',
               existing_type=mysql.VARCHAR(length=16),
               nullable=True)
        batch_op.alter_column('name',
               existing_type=mysql.VARCHAR(length=256),
               nullable=True)

    # ### end Alembic commands ###