import pytest
from unittest.mock import AsyncMock, patch
from telegram import Update, User, Message, Chat, Bot
from telegram.ext import ContextTypes

from tbot import start, menu, service_choose, master_choose, day_choose, time_choose, cancel
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_update():
    user = User(id=12345, first_name="TestUser", is_bot=False)
    chat = Chat(id=67890, type="private")
    bot = MagicMock(spec=Bot)  # Создаем мок для бота
    message = MagicMock(  # Замокаем объект Message
        message_id=1,
        date=None,
        chat=chat,
        text="/start",
        from_user=user,
    )
    message.reply_text = AsyncMock()  # Используем AsyncMock для асинхронного метода
    message._bot = bot  # Ассоциируем сообщение с ботом
    update = Update(update_id=1, message=message)
    return update




@pytest.fixture
def mock_context():
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    return context


@pytest.mark.asyncio
async def test_start_new_user(mock_update, mock_context):
    with patch("tbot.get_admin_id_by_telegram_id", return_value=None), \
         patch("tbot.get_master_id_by_telegram_id", return_value=None), \
         patch("tbot.get_client_id_by_telegram_id", return_value=None), \
         patch("tbot.add_user", return_value=1):

        next_state = await start(mock_update, mock_context)

        assert next_state == 0  # MENU
        mock_context.user_data["client_id"] = 1
        mock_update.message.reply_text.assert_called_once_with(
            "Привет! Я могу записать в салон и могу рассказать тебе о твоих записях!\n"
            "Выбери, что ты хочешь сделать?",
            reply_markup=mock_update.message.reply_text.call_args[1]["reply_markup"],
        )



@pytest.mark.asyncio
async def test_menu_book(mock_update, mock_context):
    mock_update.message.text = "Записаться"
    with patch("tbot.get_services", return_value=[AsyncMock(title="Услуга 1")]):
        next_state = await menu(mock_update, mock_context)

        assert next_state == 1
        mock_update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_service_choose_valid(mock_update, mock_context):
    mock_context.user_data["services"] = [AsyncMock(title="Услуга 1", id=1)]
    mock_update.message.text = "Услуга 1"

    with patch("tbot.get_masters_for_service", return_value=[AsyncMock(name="Мастер 1")]):
        next_state = await service_choose(mock_update, mock_context)

        assert next_state == 2
        mock_update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_master_choose_valid(mock_update, mock_context):
    mock_context.user_data["masters"] = [AsyncMock(name="Мастер 1", id=1)]
    mock_update.message.text = "Мастер 1"

    with patch("tbot.get_free_days_for_master", return_value=["2024-01-01"]):
        next_state = await master_choose(mock_update, mock_context)

        assert next_state == 3
        mock_update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_day_choose_valid(mock_update, mock_context):
    mock_context.user_data["days"] = ["2024-01-01"]
    mock_update.message.text = "2024-01-01"

    with patch("tbot.get_timeslots_for_day", return_value=[AsyncMock(time="10:00")]):
        next_state = await day_choose(mock_update, mock_context)

        assert next_state == 4
        mock_update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_time_choose_valid(mock_update, mock_context):
    mock_context.user_data.update({
        "times": ["10:00"],
        "client_id": 1,
        "service": AsyncMock(title="Услуга 1", id=1),
        "master": AsyncMock(name="Мастер 1", id=1),
        "day": "2024-01-01"
    })
    mock_update.message.text = "10:00"

    with patch("tbot.create_appointment"), \
            patch("tbot.get_calendar_link", return_value="http://calendar.link"):
        next_state = await time_choose(mock_update, mock_context)

        assert next_state == 0
        mock_update.message.reply_text.assert_called()


@pytest.mark.asyncio
async def test_cancel(mock_update, mock_context):
    next_state = await cancel(mock_update, mock_context)
    assert next_state == -1
    mock_update.message.reply_text.assert_called_once()
