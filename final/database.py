import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./eventos.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# Se estiver usando SQL Server (mssql), adicionamos argumentos extras para evitar o timeout de SSL
if DATABASE_URL.startswith("mssql"):
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"timeout": 30},
        pool_pre_ping=True
    )
else:
    engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    """Classe base dos modelos. É por ela que o SQLAlchemy descobre as tabelas."""


def get_db():
    """Entrega uma sessão para a rota e garante que ela seja fechada."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()