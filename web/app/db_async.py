from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

async_session = None


def init_async_session(app):
    """Create an async database session"""
    database_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    database_uri = database_uri.replace("postgresql", "postgresql+asyncpg")
    # database_uri = database_uri.replace("sqlite", "sqlite+aiosqlite")
    if app.config["TESTING"]:
        database_uri = database_uri.replace("sqlite:///", "sqlite+aiosqlite:///")
        print(f"Using database URI: {database_uri}")

    engine = create_async_engine(database_uri, echo=False)

    async_session_factory = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    app.extensions["async_session"] = async_session_factory
    print(f"Async session initialized: {async_session_factory}")
