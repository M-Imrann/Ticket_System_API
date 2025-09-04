from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, pool
from alembic import context

# import your Base and models (do not import models inside app.database)
from app.database import Base
# make sure this imports all model modules so metadata is populated
import app.models

# this is the Alembic Config object
config = context.config

# If you want to override the URL for alembic to use a sync driver:
sync_url = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql+psycopg2://imran:imran123@localhost:5432/ticket_db"
)
config.set_main_option("sqlalchemy.url", sync_url)

# Logging config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target metadata for `autogenerate`
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
