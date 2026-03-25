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

    op.create_table(
        "compatibility_import_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("item_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("resolved_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_compatibility_import_jobs_id", "compatibility_import_jobs", ["id"])
    op.create_index("ix_compatibility_import_jobs_item_id", "compatibility_import_jobs", ["item_id"])

    op.create_table(
        "compatibility_candidates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.String(), nullable=False),

        sa.Column("brand_name", sa.String(), nullable=True),
        sa.Column("brand_id", sa.String(), nullable=True),

        sa.Column("model_name", sa.String(), nullable=True),
        sa.Column("model_id", sa.String(), nullable=True),

        sa.Column("year_name", sa.String(), nullable=True),
        sa.Column("year_id", sa.String(), nullable=True),

        sa.Column("version_name", sa.String(), nullable=True),
        sa.Column("version_id", sa.String(), nullable=True),

        sa.Column("engine_name", sa.String(), nullable=True),
        sa.Column("engine_id", sa.String(), nullable=True),

        sa.Column("transmission_name", sa.String(), nullable=True),
        sa.Column("transmission_id", sa.String(), nullable=True),

        sa.Column("product_id", sa.String(), nullable=True),
        sa.Column("search_status", sa.String(), nullable=False),
        sa.Column("publish_status", sa.String(), nullable=False, server_default="NOT_SENT"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("search_payload", sa.Text(), nullable=True),
        sa.Column("search_response", sa.Text(), nullable=True),
        sa.Column("publish_response", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_index("ix_compatibility_candidates_id", "compatibility_candidates", ["id"])
    op.create_index("ix_compatibility_candidates_job_id", "compatibility_candidates", ["job_id"])
    op.create_index("ix_compatibility_candidates_item_id", "compatibility_candidates", ["item_id"])
    op.create_index("ix_compatibility_candidates_product_id", "compatibility_candidates", ["product_id"])
    op.create_index("ix_compatibility_candidates_search_status", "compatibility_candidates", ["search_status"])
    op.create_index("ix_compatibility_candidates_publish_status", "compatibility_candidates", ["publish_status"])


def downgrade():
    op.drop_index("ix_compatibility_candidates_publish_status", table_name="compatibility_candidates")
    op.drop_index("ix_compatibility_candidates_search_status", table_name="compatibility_candidates")
    op.drop_index("ix_compatibility_candidates_product_id", table_name="compatibility_candidates")
    op.drop_index("ix_compatibility_candidates_item_id", table_name="compatibility_candidates")
    op.drop_index("ix_compatibility_candidates_job_id", table_name="compatibility_candidates")
    op.drop_index("ix_compatibility_candidates_id", table_name="compatibility_candidates")
    op.drop_table("compatibility_candidates")

    op.drop_index("ix_compatibility_import_jobs_item_id", table_name="compatibility_import_jobs")
    op.drop_index("ix_compatibility_import_jobs_id", table_name="compatibility_import_jobs")
    op.drop_table("compatibility_import_jobs")

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