from playwright.async_api import async_playwright, Page, BrowserContext
from core.computer.interfaces import BrowserController
from infrastructure.logging import get_logger

logger = get_logger("infrastructure.browser")

class PlaywrightBrowserController(BrowserController):
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context: BrowserContext = None
        self.page: Page = None
        self._is_initialized = False

    async def _ensure_initialized(self):
        if not self._is_initialized:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=False)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            self._is_initialized = True
            logger.debug("Playwright browser initialized")

    async def open_url(self, url: str) -> None:
        await self.navigate(url)

    async def get_current_url(self) -> str:
        if not self.page:
            return ""
        return self.page.url

    async def get_page_title(self) -> str:
        if not self.page:
            return ""
        return await self.page.title()

    async def navigate(self, url: str) -> None:
        await self._ensure_initialized()
        if not url.startswith("http"):
            url = "https://" + url
        await self.page.goto(url)
        logger.debug("Navigated to URL", url=url)

    async def go_back(self) -> None:
        if self.page:
            await self.page.go_back()

    async def go_forward(self) -> None:
        if self.page:
            await self.page.go_forward()

    async def refresh(self) -> None:
        if self.page:
            await self.page.reload()

    async def click(self, selector: str) -> None:
        if self.page:
            await self.page.click(selector)

    async def type(self, selector: str, text: str) -> None:
        if self.page:
            await self.page.fill(selector, text)

    async def scroll(self, amount: int) -> None:
        if self.page:
            await self.page.mouse.wheel(0, amount)

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self._is_initialized = False
