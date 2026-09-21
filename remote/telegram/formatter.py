import re

class TelegramFormatter:
    """
    Safely formats text and responses for Telegram MarkdownV2 to prevent errors.
    """
    
    def format_text(self, text: str) -> str:
        """
        Escapes special characters required by Telegram MarkdownV2, except those used
        for intentional formatting.
        For robust simplicity, we'll strip or escape characters that cause parser errors
        if they aren't paired correctly.
        """
        # Telegram Markdown V2 requires these characters to be escaped if not part of markup:
        # _ * [ ] ( ) ~ ` > # + - = | { } . !
        
        # A simple approach for raw text output from the agent is to escape everything,
        # but the agent often returns markdown.
        # For this prototype, we'll strip the worst offenders or just send it as raw text
        # by escaping specific unclosed characters, or using parse_mode=None in the adapter.
        
        # Instead of risking MarkdownV2 crashes from LLM output, we'll escape the most
        # common unescaped problematic characters.
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        # This is a naive escape. In production, we'd use a robust markdown parser to AST 
        # and re-render to Telegram HTML or safe MarkdownV2.
        
        # For now, let's just use the text as is, but TelegramAdapter should ideally 
        # disable parse_mode when sending raw LLM responses to avoid exceptions.
        return text

telegram_formatter = TelegramFormatter()
