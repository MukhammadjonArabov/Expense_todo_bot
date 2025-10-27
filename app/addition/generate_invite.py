from app.config import BOT_USERNAME

def generate_invite_link(token: str) -> str:
    return f"https://t.me/{BOT_USERNAME}?start=join_{token}"
