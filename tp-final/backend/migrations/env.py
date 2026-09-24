import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from pulso.config import Settings
from pulso.models import Base

config = context.config
if config.config_file_name and config.attributes.get('configure_logger', True):
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def database_url() -> str:
    # Tests pass an explicit URL; otherwise DATABASE_URL.
    return (
        config.attributes.get('database_url')
        or os.environ.get('DATABASE_URL')
        or Settings.model_fields['database_url'].default
    )


def run_migrations_offline() -> None:
    context.configure(url=database_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(database_url())
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
