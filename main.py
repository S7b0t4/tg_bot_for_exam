import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import F
from database import createUser, createTask, getStatus, getRandomTask

api_token = '7358477783:AAFqhM5DZUWF18keUNoFC0EV6I5PZrlxD50'
bot = Bot(token=api_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

@dp.message(Command('start'))
async def cmd_start(message:Message):
    user = message.from_user
    await createUser(user.id, user.username)
    keyboard1 = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Практика по заданиям', callback_data='practice')],
        [InlineKeyboardButton(text='Мой профиль', callback_data='profile')],
        [InlineKeyboardButton(text='Добавить задачу', callback_data='add_task')]
    ])
    await message.answer('Привет! Это бот для практики по заданиям из ЕГЭ по физике.', reply_markup=keyboard1)

# Фильтры для кнопок

@dp.callback_query(F.data == 'practice')
async def practice_handler(callback: CallbackQuery):
    keyboard2 = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Задание номер 18', callback_data='task_18')],
        [InlineKeyboardButton(text='Назад', callback_data='start')]
    ])
    await callback.message.answer('Выбери раздел:', reply_markup=keyboard2)

class TaskPracticeState(StatesGroup):
    waiting_for_answer = State()

@dp.callback_query(F.data == 'task_18')
async def send_task_18(callback: CallbackQuery, state: FSMContext):
    task = await getRandomTask()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Правильный", callback_data="answer_right")],
        [InlineKeyboardButton(text="❌ Неправильный", callback_data="answer_wrong")],
        [InlineKeyboardButton(text='Назад', callback_data='start')]
    ])

    sent = await callback.message.answer(task["description"], reply_markup=keyboard)
    await state.set_state(TaskPracticeState.waiting_for_answer)
    await state.update_data(
    task_id=task["id"],
    is_right=task["is_right_answer"],
    description_answer=task["description_answer"],
    message_ids=[sent.message_id]
)


@dp.callback_query(TaskPracticeState.waiting_for_answer)
async def check_answer(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    correct_answer = data["is_right"]
    message_ids = data.get("message_ids", [])

    # Удаление старых сообщений по списку
    for msg_id in message_ids:
        try:
            await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
        except Exception as e:
            print(f"❌ Не удалось удалить сообщение {msg_id}: {e}")

    # Проверка ответа
    user_answer = callback.data == "answer_right"
    result_msg = await callback.message.answer("✅ Верно!" if user_answer == correct_answer else "❌ Неверно!")
    explanation_msg = await callback.message.answer(data["description_answer"])

    # ⏳ Удаление этих двух сообщений — в фоне (через 10 сек)
    async def delayed_cleanup():
        await asyncio.sleep(5)
        for msg in [result_msg, explanation_msg]:
            try:
                await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=msg.message_id)
            except Exception as e:
                print(f"❌ Не удалось удалить сообщение: {e}")

    asyncio.create_task(delayed_cleanup())

    await state.clear()

    # ⏱️ Новый вопрос — сразу
    await send_task_18(callback, state)



@dp.callback_query(F.data == 'profile')
async def profile_handler(callback: CallbackQuery):
    status = await getStatus(callback.from_user.id)
    print(status)
    keyboard3 = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Назад', callback_data='start')]
    ])
    await callback.message.answer(
    f'<b>Профиль пользователя👤</b>\n'
    f'Пройдено заданий: {status["total_tasks"]}\n'
    f'Отвечено правильно: {status["correct"]}\n'
    f'Отвечено неправильно: {status["wrong"]}',
    reply_markup=keyboard3
    )


#Добавить задачу

class AddTaskState(StatesGroup):
    waiting_for_task_text = State()
    waiting_for_answer_type = State()

@dp.callback_query(F.data == 'add_task')
async def add_task_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddTaskState.waiting_for_task_text)
    keyboard2 = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Назад', callback_data='start')]
    ])
    await callback.message.answer('Введите описание:', reply_markup=keyboard2)

@dp.message(AddTaskState.waiting_for_task_text)
async def get_task_text(message: Message, state: FSMContext):
    await state.update_data(task_text=message.text)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Правильный", callback_data="answer_right")],
        [InlineKeyboardButton(text="❌ Неправильный", callback_data="answer_wrong")],
        [InlineKeyboardButton(text='Назад', callback_data='start')]
    ])

    await message.answer("Это правильный ответ или неправильный?", reply_markup=keyboard)
    await state.set_state(AddTaskState.waiting_for_answer_type)

@dp.callback_query(AddTaskState.waiting_for_answer_type)
async def get_answer_type(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'start':
        await state.clear()
        await callback.message.answer("Отменено. Возвращаюсь в главное меню.")
        await cmd_start(callback.message)
        await callback.answer()
        return

    data = await state.get_data()
    task_text = data['task_text']

    is_right = callback.data == "answer_right"

    # Здесь можно сохранить в БД, например:
    await createTask(task_text, is_right)

    await callback.message.answer("Задача добавлена ✅")
    await state.clear()


#Назад

@dp.callback_query(F.data == 'start')
async def practice_handler(callback: CallbackQuery):
    await cmd_start(callback.message)
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())