from alembic import op
import sqlalchemy as sa

revision = "20260324_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "vehicle_brands",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
    )
    op.create_index("ix_vehicle_brands_id", "vehicle_brands", ["id"])
    op.create_index("ix_vehicle_brands_name", "vehicle_brands", ["name"])

    op.create_table(
        "vehicle_models",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
    )
    op.create_index("ix_vehicle_models_id", "vehicle_models", ["id"])
    op.create_index("ix_vehicle_models_name", "vehicle_models", ["name"])

    op.create_table(
        "vehicle_years",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
    )
    op.create_index("ix_vehicle_years_id", "vehicle_years", ["id"])
    op.create_index("ix_vehicle_years_name", "vehicle_years", ["name"])

    op.create_table(
        "vehicle_versions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
    )
    op.create_index("ix_vehicle_versions_id", "vehicle_versions", ["id"])
    op.create_index("ix_vehicle_versions_name", "vehicle_versions", ["name"])

    op.create_table(
        "vehicle_engines",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
    )
    op.create_index("ix_vehicle_engines_id", "vehicle_engines", ["id"])
    op.create_index("ix_vehicle_engines_name", "vehicle_engines", ["name"])

    op.create_table(
        "vehicle_transmissions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
    )
    op.create_index("ix_vehicle_transmissions_id", "vehicle_transmissions", ["id"])
    op.create_index("ix_vehicle_transmissions_name", "vehicle_transmissions", ["name"])


def downgrade():
    op.drop_index("ix_vehicle_transmissions_name", table_name="vehicle_transmissions")
    op.drop_index("ix_vehicle_transmissions_id", table_name="vehicle_transmissions")
    op.drop_table("vehicle_transmissions")

    op.drop_index("ix_vehicle_engines_name", table_name="vehicle_engines")
    op.drop_index("ix_vehicle_engines_id", table_name="vehicle_engines")
    op.drop_table("vehicle_engines")

    op.drop_index("ix_vehicle_versions_name", table_name="vehicle_versions")
    op.drop_index("ix_vehicle_versions_id", table_name="vehicle_versions")
    op.drop_table("vehicle_versions")

    op.drop_index("ix_vehicle_years_name", table_name="vehicle_years")
    op.drop_index("ix_vehicle_years_id", table_name="vehicle_years")
    op.drop_table("vehicle_years")

    op.drop_index("ix_vehicle_models_name", table_name="vehicle_models")
    op.drop_index("ix_vehicle_models_id", table_name="vehicle_models")
    op.drop_table("vehicle_models")

    op.drop_index("ix_vehicle_brands_name", table_name="vehicle_brands")
    op.drop_index("ix_vehicle_brands_id", table_name="vehicle_brands")
    op.drop_table("vehicle_brands")