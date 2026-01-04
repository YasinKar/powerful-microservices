from sqlmodel import Session, create_engine

from core.config import settings


engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


def init_db(session: Session) -> None:
    # if you don't want to use migrations, create the tables un-commenting the next lines
    
    # from sqlmodel import SQLModel
    # SQLModel.metadata.create_all(engine)

    pass