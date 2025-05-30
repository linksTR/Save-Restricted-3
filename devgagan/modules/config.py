import os

class Config:
    """
    Botun yapılandırma ayarlarını ortam değişkenlerinden alır.
    """
    API_ID = int(os.environ.get("API_ID", 0))  # int() ile tam sayıya çeviriyoruz
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    USERBOT_SESSION_STRING = os.environ.get("STRING", None) # Userbot için, isteğe bağlı

    # Gerekli değişkenlerin kontrolü
    if not all([API_ID, API_HASH, BOT_TOKEN]):
        raise ValueError("Ortam değişkenleri (API_ID, API_HASH, BOT_TOKEN) eksik veya hatalı. Lütfen kontrol edin.")

    # Not: İstersen buraya log kanalı ID'si gibi ek değişkenler de ekleyebilirsin:
    # LOG_CHANNEL_ID = int(os.environ.get("LOG_CHANNEL_ID", 0))
