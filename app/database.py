import  os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, BigInteger

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

eginer = create_async_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=eginer, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True)
    username = Column(String)
    user_link = Column(String, nullable=True)
    phone = Column(String, nullable=True)

async def init_db():
    async with eginer.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def add_user(tg_id, username, user_link, phone):
    async with Session() as session:
        user = User(
            id=tg_id,
            username=username,
            user_link=user_link,
            phone=phone
        )
        session.add(user)
        try:
            await session.commit()
        except:
            await session.rollback()
