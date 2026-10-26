# Safety check: every registered handler must declare who may use it.


import sys

from app.telegram_bot.bot import build_application


def main() -> int:
    application = build_application()
    unprotected = 0
    for handlers in application.handlers.values():
        for handler in handlers:
            callback = handler.callback
            level = getattr(callback, "auth_level", None)
            print(f"{callback.__name__:<26} {level or 'UNPROTECTED   <-- fix this'}")
            if level is None:
                unprotected += 1
    print(f"\n{unprotected} unprotected handler(s).")
    return 1 if unprotected else 0


if __name__ == "__main__":
    sys.exit(main())