"""Move email and phone to order

Revision ID: abcd066a1ed9
Revises: 2fb2bdf8e153
Create Date: 2020-09-11 11:54:02.963854

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'abcd066a1ed9'
down_revision = '2fb2bdf8e153'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('information', 'email')
    op.drop_column('information', 'phone')
    op.add_column('order', sa.Column('email', sa.String(length=150), nullable=True))
    op.add_column('order', sa.Column('phone', sa.String(length=20), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('order', 'phone')
    op.drop_column('order', 'email')
    op.add_column('information', sa.Column('phone', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=20), nullable=True))
    op.add_column('information', sa.Column('email', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=150), nullable=True))
    # ### end Alembic commands ###
