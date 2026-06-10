"""
Configuración de la base de datos con SQLAlchemy 2.0 async.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# Motor async de SQLAlchemy
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,       # Mostrar SQL en modo debug
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,        # Verificar conexiones antes de usarlas
)

# Factoría de sesiones
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base declarativa para todos los modelos ORM."""
    pass


async def init_db():
    """Crea todas las tablas definidas en los modelos."""
    # Importar modelos para que Base los registre
    from app.models import job  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """
    Dependency de FastAPI: proporciona una sesión de base de datos
    y garantiza que se cierra al terminar la petición.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
