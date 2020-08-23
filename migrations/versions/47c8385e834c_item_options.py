"""Item options

Revision ID: 47c8385e834c
Revises: cce76269f296
Create Date: 2020-08-22 20:47:38.777639

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '47c8385e834c'
down_revision = 'cce76269f296'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('item', sa.Column('option_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'item', 'option', ['option_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'item', type_='foreignkey')
    op.drop_column('item', 'option_id')
    # ### end Alembic commands ###
