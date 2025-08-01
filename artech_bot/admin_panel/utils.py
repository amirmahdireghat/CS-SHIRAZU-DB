# utils.py
from django.core.cache import cache
from .models import bot_text

async def get_bot_text(key, default=""):
    cache_key = f"bot_text_{key}"
    content = cache.get(cache_key)
    if content is None:
        try:
            bot_text_instance = await bot_text.objects.aget(key=key)
            content = bot_text_instance.content
            cache.set(cache_key, content, timeout=900)  # Cache for 15 minuts
        except bot_text.DoesNotExist:
            content = default
    return content