"""fixes for security-too

Revision ID: 552aa61f076d
Revises: 3a138af3da91
Create Date: 2023-06-20 09:15:18.304523

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '552aa61f076d'
down_revision = '3a138af3da91'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('username',
               existing_type=mysql.VARCHAR(length=255),
               type_=sa.String(length=3),
               nullable=False)
        batch_op.drop_index('alias')
        batch_op.drop_column('alias')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('alias', mysql.VARCHAR(length=3), nullable=False))
        batch_op.create_index('alias', ['alias'], unique=False)
        batch_op.alter_column('username',
               existing_type=sa.String(length=3),
               type_=mysql.VARCHAR(length=255),
               nullable=True)

    # ### end Alembic commands ###
