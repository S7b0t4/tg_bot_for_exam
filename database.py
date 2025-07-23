from sqlalchemy import Column, Integer, String, BigInteger, Boolean, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import asyncio

DATABASE_URL = 'postgresql+asyncpg://user:password@77.91.70.186:6543/fizegebot'
engine = create_async_engine(DATABASE_URL, future=True, echo=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, primary_key=True, default=0)
    username = Column(String)
    total_tasks = Column(Integer, default=0)
    correct = Column(Integer, default=0)
    wrong = Column(Integer, default=0)

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String)
    is_right_answer = Column(Boolean, default=True)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

#Функция которая добавляет пользователя в базу если его нету
async def get_user(session: AsyncSession, tg_id: BigInteger, username: str = None) -> User:
    print(tg_id, username)
    #Здесь она находит пользователя
    result = await session.execute(
        select(User).where(User.tg_id == tg_id)
    )
    user = result.scalar_one_or_none()

    #А здесь если не находит то создает либо меняет имя пользователя если у него поменялось tg_tag
    if not user:
        user = User(tg_id=tg_id, username=username)
        session.add(user)
        await session.commit()
    elif username and user.username != username:
        user.username = username
        await session.commit()
    print(user.id, user.username, user.total_tasks)
    return user

#Функция которая создает задание
async def get_task(session: AsyncSession, task_text: str, is_right: Boolean) -> Task:
    task = Task(description=task_text, is_right_answer=is_right)
    session.add(task)
    await session.commit()
    return task

#Функция которая ищет пользователя по tg_id
async def get_status(session: AsyncSession, tg_id:BigInteger) -> User:
    result = await session.execute(
        select(User).where(User.tg_id == tg_id)
    )
    return result


async def main():
    await init_db()

async def createUser(tg_id, username):
    async with async_session() as session:
        user = await get_user(session, tg_id=tg_id, username=username)

async def createTask(task_text, is_right):
    async with async_session() as session:
        task = await get_task(session, task_text=task_text, is_right=is_right)

async def getStatus(tg_id):
    async with async_session() as session:
        status = await get_status(session, tg_id=tg_id)
        return status

if __name__ == '__main__':
    asyncio.run(main())