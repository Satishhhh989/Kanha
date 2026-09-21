import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from core.config import settings
from remote.authentication.identity import auth_manager
from infrastructure.logging.audit import audit_logger
from remote.sessions.manager import remote_sessions
from aiogram.types import BufferedInputFile, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from core.computer.factory import get_computer_controller
from core.computer.models import Point

logger = logging.getLogger("core.remote.telegram")

class TelegramAdapter:
    """
    Acts as the entry point for Telegram remote commands.
    Long-polls Telegram for updates and routes them to the Agent Runtime.
    """
    
    def __init__(self):
        self.token = settings.telegram_bot_token
        self.bot = None
        self.dp = None
        self._polling_task = None
        
        if self.token:
            self.bot = Bot(
                token=self.token, 
                default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2)
            )
            self.dp = Dispatcher()
            self._register_handlers()

    def _register_handlers(self):
        # Register explicit commands
        self.dp.message(Command("start", "status"))(self.handle_status)
        
        # Register callback query handler for inline keyboards
        self.dp.callback_query()(self.handle_callback)
        
        # Register fallback natural language handler
        self.dp.message()(self.handle_natural_language)
        
    async def _is_authorized(self, message: types.Message) -> bool:
        """Centralized middleware-like check for authorization and rate limits."""
        user_id = message.from_user.id
        
        if not auth_manager.authenticate_telegram_user(user_id):
            await message.reply(
                f"⛔️ *Unauthorized Account*\n\nYour Telegram User ID is: `{user_id}`\n\nTo allow this account to control KAHNA, add this ID to `TELEGRAM_ALLOWED_USER_ID` in your `.env` file:\n`TELEGRAM_ALLOWED_USER_ID=...,{user_id}`",
                parse_mode="Markdown"
            )
            return False
            
        # 2. Check Rate Limit (max 5 commands per 10 seconds)
        now = asyncio.get_event_loop().time()
        if not hasattr(self, '_rate_limits'):
            self._rate_limits = {}
            
        user_history = self._rate_limits.get(user_id, [])
        # Clean old timestamps
        user_history = [t for t in user_history if now - t < 10.0]
        
        if len(user_history) >= 5:
            audit_logger._log_event("RATE_LIMIT_EXCEEDED", user_id=str(user_id))
            await message.reply("⚠️ Rate limit exceeded. Please wait a moment.")
            return False
            
        user_history.append(now)
        self._rate_limits[user_id] = user_history
        
        return True

    async def handle_status(self, message: types.Message):
        """Returns a safe remote status summary."""
        if not await self._is_authorized(message):
            return
            
        audit_logger.log_remote_command(str(message.from_user.id), message.text)
        
        # Generate status text
        status_text = (
            "🤖 *KAHNA ONLINE*\n"
            f"Device: `{settings.kahna_device_id}`\n"
            "Agent: `READY`\n"
            "Computer Control: `AVAILABLE`\n"
            "Screen: `AVAILABLE`\n"
        )
        
        # Escape markdown v2 reserved characters except the ones we use for formatting
        # Basic markdown v2 requires escaping certain characters like hyphens, periods, etc.
        # But we will use aiogram's safe escaping or just raw formatting if careful.
        await message.reply(status_text)

    async def handle_natural_language(self, message: types.Message):
        """Routes natural language to the Agent Runtime."""
        if not await self._is_authorized(message):
            return
            
        user_id_str = str(message.from_user.id)
        audit_logger.log_remote_command(user_id_str, message.text)
        
        # Get or create isolated session for this user
        session_id = remote_sessions.get_or_create_session(user_id_str)
        
        # We should ideally indicate typing while KAHNA thinks
        await self.bot.send_chat_action(chat_id=message.chat.id, action="typing")
        
        try:
            from core.agent import agent_runtime
            response = await agent_runtime.chat(session_id, message.text)
            
            # Simple text response for now, phase 4 step 3 will expand this
            if response:
                await message.reply(response, parse_mode=None)
            else:
                await message.reply("Done.", parse_mode=None)
                
        except Exception as e:
            logger.error(f"Error processing remote natural language command: {e}")
            await message.reply(f"⚠️ KAHNA encountered an error:\n{e}")

    async def handle_callback(self, query: types.CallbackQuery):
        """Handles inline keyboard callbacks (like confirmations or quick actions)."""
        data = query.data
        if not data:
            return
            
        if data.startswith("conf:"):
            _, decision, request_id = data.split(":")
            
            from remote.sessions.confirmations import confirmation_manager
            approved = (decision == "yes")
            success = confirmation_manager.resolve_request(request_id, approved)
            
            user_id_str = str(query.from_user.id)
            audit_logger.log_confirmation_resolved(user_id_str, "REMOTE_TOOL", approved)
            
            if success:
                await query.message.edit_text(
                    f"✅ Confirmation {'approved' if approved else 'denied'}.", 
                    reply_markup=None
                )
            else:
                await query.answer("This confirmation request has expired or is invalid.", show_alert=True)
                await query.message.edit_text("❌ Confirmation expired.", reply_markup=None)
                
        elif data.startswith("action:"):
            action = data.split(":")[1]
            if action == "screenshot":
                await self._handle_interactive_screen(query)
            elif action == "launch_app":
                await self.bot.send_message(query.from_user.id, "Type `open [app name]` to launch an application.", parse_mode="Markdown")
                await query.answer()
            elif action.startswith("mouse_"):
                await self._handle_mouse_action(query, action)
            elif action == "keyboard":
                await self.bot.send_message(query.from_user.id, "Type `type [text]`.", parse_mode="Markdown")
                await query.answer()
            else:
                await query.answer()
        else:
            await query.answer()

    def _get_interactive_markup(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="↖️", callback_data="action:mouse_upleft"),
                InlineKeyboardButton(text="⬆️", callback_data="action:mouse_up"),
                InlineKeyboardButton(text="↗️", callback_data="action:mouse_upright")
            ],
            [
                InlineKeyboardButton(text="⬅️", callback_data="action:mouse_left"),
                InlineKeyboardButton(text="🖱 Click", callback_data="action:mouse_click"),
                InlineKeyboardButton(text="➡️", callback_data="action:mouse_right")
            ],
            [
                InlineKeyboardButton(text="↙️", callback_data="action:mouse_downleft"),
                InlineKeyboardButton(text="⬇️", callback_data="action:mouse_down"),
                InlineKeyboardButton(text="↘️", callback_data="action:mouse_downright")
            ],
            [
                InlineKeyboardButton(text="🔄 Refresh", callback_data="action:mouse_refresh")
            ]
        ])

    async def _handle_interactive_screen(self, query: types.CallbackQuery):
        """Sends the initial interactive screen view."""
        controller = get_computer_controller()
        frame = await controller.screen.capture_primary_screen()
        
        await query.answer("Fetching screen...")
        
        photo = BufferedInputFile(frame.image_data, filename="screen.png")
        await self.bot.send_photo(
            chat_id=query.from_user.id,
            photo=photo,
            caption="*Interactive Screen Session*\nUse the buttons below to control the mouse.",
            reply_markup=self._get_interactive_markup(),
            parse_mode="Markdown"
        )

    async def _handle_mouse_action(self, query: types.CallbackQuery, action: str):
        """Handles mouse movement and clicks, then updates the screen."""
        controller = get_computer_controller()
        
        if action != "mouse_refresh":
            if action == "mouse_click":
                await controller.mouse.click()
            else:
                # Directional movement
                pos = await controller.mouse.get_position()
                step = 100 # Move 100 pixels per tap
                
                new_x, new_y = pos.x, pos.y
                if "up" in action:
                    new_y -= step
                if "down" in action:
                    new_y += step
                if "left" in action:
                    new_x -= step
                if "right" in action:
                    new_x += step
                
                await controller.mouse.move(Point(x=new_x, y=new_y))
                
        # Take a fresh screenshot and update the message media
        frame = await controller.screen.capture_primary_screen()
        media = InputMediaPhoto(
            media=BufferedInputFile(frame.image_data, filename="screen.png"),
            caption="*Interactive Screen Session*\nUse the buttons below to control the mouse.",
            parse_mode="Markdown"
        )
        
        try:
            await query.message.edit_media(media=media, reply_markup=self._get_interactive_markup())
        except Exception as e:
            logger.error(f"Failed to update screen media: {e}")
            
        await query.answer()

    async def start(self):
        """Starts the Telegram polling loop."""
        if not self.bot:
            logger.warning("TELEGRAM_BOT_TOKEN not set. Remote access disabled.")
            return
            
        logger.info("Starting Telegram Remote Gateway...")
        
        # Subscribe to Event Bus for confirmations
        from core.events.bus import event_bus
        from core.events.models import EventType
        self._event_sub = event_bus.subscribe(
            EventType.TOOL_CALL_STARTED, 
            self._handle_agent_events
        )
        
        # Drop pending updates to avoid processing stale commands after restart
        await self.bot.delete_webhook(drop_pending_updates=True)
        
        # Send startup notification to authorized user
        if auth_manager.allowed_user_id:
            try:
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                markup = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="📸 Screen", callback_data="action:screenshot"),
                        InlineKeyboardButton(text="🚀 Launch App", callback_data="action:launch_app")
                    ],
                    [
                        InlineKeyboardButton(text="🖱 Mouse", callback_data="action:mouse"),
                        InlineKeyboardButton(text="⌨️ Keyboard", callback_data="action:keyboard")
                    ]
                ])
                await self.bot.send_message(
                    chat_id=int(auth_manager.allowed_user_id),
                    text="🟢 *KAHNA is Online!*\n\nDirect local control is enabled. You can use the buttons below or type natural language commands (e.g. `open Safari`).",
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Failed to send startup message: {e}")
        
        try:
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Telegram polling failed: {e}")

    async def _handle_agent_events(self, event):
        """Intercepts backend events to render Telegram UI like inline keyboards."""
        if event.event_type == "TOOL_CALL_STARTED" and event.payload.get("action") == "REQUIRE_CONFIRMATION":
            user_id_str = event.session_id.split("-")[1]
            request_id = event.payload.get("request_id")
            tool_name = event.payload.get("tool_name")
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Confirm", callback_data=f"conf:yes:{request_id}"),
                    InlineKeyboardButton(text="❌ Cancel", callback_data=f"conf:no:{request_id}")
                ]
            ])
            
            try:
                await self.bot.send_message(
                    chat_id=int(user_id_str),
                    text=f"⚠️ *KAHNA requires confirmation*\n\nAction: `{tool_name}`",
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Failed to send confirmation keyboard: {e}")

    async def stop(self):
        """Stops the Telegram polling loop."""
        if hasattr(self, '_event_sub') and self._event_sub:
            from core.events.bus import event_bus
            event_bus.unsubscribe(self._event_sub)
            
        if self.bot:
            logger.info("Stopping Telegram Remote Gateway...")
            await self.bot.session.close()

# Global singleton
telegram_adapter = TelegramAdapter()
