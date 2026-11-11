"""convert_grade_to_enum

Revision ID: d18136c9e8e0
Revises: 03b4cc3a39fa
Create Date: 2026-09-02 20:42:20.812760

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'd18136c9e8e0'
down_revision = '03b4cc3a39fa'
branch_labels = None
depends_on = None


def upgrade():
    grade_enum = sa.Enum(
        "A", "B", "C", "D", "F", "W", "I",
        name="grade_letter_enum"
    )
    grade_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "courses",
        sa.Column(
            "grade",
            grade_enum,
            nullable=True
        )
    )


def downgrade():
    op.drop_column("courses", "grade")

    grade_enum = sa.Enum(
        "A", "B", "C", "D", "F", "W", "I",
        name="grade_letter_enum"
    )
    grade_enum.drop(op.get_bind(), checkfirst=True)
