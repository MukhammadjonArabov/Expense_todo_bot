import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, select, BigInteger, ForeignKey, DateTime, func

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL .env faylda topilmadi!")

Base = declarative_base()

engine = create_async_engine(
    DATABASE_URL,
    echo=True
)

async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)  # O'zgartirildi
    username = Column(String, nullable=True)
    user_link = Column(String, nullable=True)
    phone = Column(String, nullable=False)

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)    

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Jadval(lar) yaratildi.")

async def add_user(tg_id: int, username: str = None, user_link: str = None, phone: str = None):
    if phone is None:
        raise ValueError("Telefon raqam majburiy!")
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == tg_id))
        existing_user = result.scalars().first()

        if existing_user:
            print("⚠️ Foydalanuvchi allaqachon bazada bor.")
            return existing_user

        new_user = User(
            telegram_id=tg_id,
            username=username,
            user_link=user_link,
            phone=phone
        )
        session.add(new_user)
        await session.commit()
        print("✅ Yangi foydalanuvchi qo‘shildi.")
        return new_user