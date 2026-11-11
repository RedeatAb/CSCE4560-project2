"""split_professor_name_and_aggregate_weights

Revision ID: d81d8262bf75
Revises: d18136c9e8e0
Create Date: 2026-09-02 21:08:47.850131

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'd81d8262bf75'
down_revision = 'd18136c9e8e0'
branch_labels = None
depends_on = None


def upgrade():
    # Add the new professor name columns as nullable first
    op.add_column(
        "professors",
        sa.Column("first_name", sa.String(), nullable=True)
    )
    op.add_column(
        "professors",
        sa.Column("last_name", sa.String(), nullable=True)
    )

    # Preserve existing professor names by splitting full_name
    op.execute(
        """
        UPDATE professors
        SET
            first_name = split_part(trim(full_name), ' ', 1),
            last_name = CASE
                WHEN position(' ' in trim(full_name)) > 0
                THEN substring(
                    trim(full_name)
                    FROM position(' ' in trim(full_name)) + 1
                )
                ELSE ''
            END
        """
    )

    # After the data has been copied, enforce NOT NULL
    op.alter_column(
        "professors",
        "first_name",
        existing_type=sa.String(),
        nullable=False,
    )
    op.alter_column(
        "professors",
        "last_name",
        existing_type=sa.String(),
        nullable=False,
    )

    # Remove the old full_name column
    op.drop_column("professors", "full_name")

    # Add total allocated task weight to courses
    op.add_column(
        "courses",
        sa.Column(
            "total_allocated_weight",
            sa.Numeric(),
            nullable=True,
        ),
    )

    # Calculate the total task weight for every course
    op.execute(
        """
        UPDATE courses
        SET total_allocated_weight = COALESCE(
            (
                SELECT SUM(course_tasks.weight)
                FROM course_tasks
                WHERE course_tasks.course_id = courses.id
            ),
            0
        )
        """
    )


def downgrade():
    # Restore the original full_name column
    op.add_column(
        "professors",
        sa.Column("full_name", sa.String(), nullable=True)
    )

    # Rebuild full_name without losing professor data
    op.execute(
        """
        UPDATE professors
        SET full_name = trim(
            concat_ws(' ', first_name, last_name)
        )
        """
    )

    op.alter_column(
        "professors",
        "full_name",
        existing_type=sa.String(),
        nullable=False,
    )

    # Remove the Phase 5 professor columns
    op.drop_column("professors", "last_name")
    op.drop_column("professors", "first_name")

    # Remove the calculated course field
    op.drop_column("courses", "total_allocated_weight")
