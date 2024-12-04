from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

async_session = None


def init_async_session(app):
    database_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    database_uri = database_uri.replace("postgresql", "postgresql+asyncpg")

    engine = create_async_engine(database_uri, echo=False)

    async_session_factory = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    app.extensions["async_session"] = async_session_factory
    print(f"Async session initialized: {async_session}")
