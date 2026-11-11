"""add shopping cart models

Revision ID: 0b29a77d7d87
Revises: d81d8262bf75
Create Date: 2026-09-27 09:29:16.998372

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '0b29a77d7d87'
down_revision = 'd81d8262bf75'
branch_labels = None
depends_on = None


def upgrade():
   
    op.create_table('shoppingcart',
    sa.Column('session_key', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('expires', sa.DateTime(), nullable=False),
    sa.Column('total', sa.Numeric(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('cartitem',
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('unit_price', sa.Numeric(), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('item_id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['item_id'], ['item.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('cartitem_shoppingcart_link',
    sa.Column('cart_item_id', sa.Uuid(), nullable=False),
    sa.Column('shopping_cart_id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['cart_item_id'], ['cartitem.id'], ),
    sa.ForeignKeyConstraint(['shopping_cart_id'], ['shoppingcart.id'], ),
    sa.PrimaryKeyConstraint('cart_item_id', 'shopping_cart_id')
    )
    
    # ### end Alembic commands ###


def downgrade():
   
    
    op.drop_table('cartitem_shoppingcart_link')
    op.drop_table('cartitem')
    op.drop_table('shoppingcart')
    # ### end Alembic commands ###
