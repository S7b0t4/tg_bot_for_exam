from sqlalchemy import Column, Integer, String, BigInteger, Boolean, select, func
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
    description_answer = Column(String)
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
    user = result.scalar_one_or_none()

    if user is not None:
        user_dict = sqlalchemy_obj_to_dict(user)
        return user_dict

async def get_random_task(session: AsyncSession) -> Task:
    result = await session.execute(
    select(Task).order_by(func.random()).limit(1)
    )
    task = result.scalar_one_or_none()

    if task is not None:
        task_dict = sqlalchemy_obj_to_dict(task)
        return task_dict

async def update_user_stats(session: AsyncSession, tg_id:BigInteger, answer: Boolean) -> User:
    result = await session.execute(
        select(User).where(User.tg_id == tg_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        return

    user.total_tasks += 1
    if answer:
        user.correct += 1
    else:
        user.wrong += 1
    
    await session.commit()


def sqlalchemy_obj_to_dict(obj):
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


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

async def getRandomTask():
    async with async_session() as session:
        status = await get_random_task(session)
        return status

async def updateUserStats(tg_id, answer):
    async with async_session() as session:
        status = await update_user_stats(session, tg_id=tg_id, answer=answer)
        return status

if __name__ == '__main__':
    asyncio.run(main())