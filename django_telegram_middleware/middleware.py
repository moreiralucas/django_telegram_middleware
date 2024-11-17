import logging
import requests
import multiprocessing

from django.http.response import HttpResponse
from django.core.handlers.wsgi import WSGIRequest
from django.conf import settings
from logging import Logger


logger: Logger = logging.getLogger()


class DjangoTelegramMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        assert hasattr(settings, 'TELEGRAM_BOT_TOKEN'), "You need put the 'TELEGRAM_BOT_TOKEN' key in django settings."
        assert hasattr(settings, 'TELEGRAM_CHAT_ID'), "You need put the 'TELEGRAM_CHAT_ID' key in django settings."

    def __call__(self, request):
        response = self.get_response(request)

        if response.status_code >= 400 and getattr(settings, "DJANGO_TELEGRAM_MIDDLEWARE", False) is True and not getattr(settings, "DEBUG", True) and response.status_code not in getattr(settings, "DJANGO_TELEGRAM_DENIED_LIST", []):
            self.send_telegram_message(request, response)

        return response

    def send_telegram_message(self, request: WSGIRequest, response: HttpResponse):
        def send_message_in_process():
            telegram_bot_token = settings.TELEGRAM_BOT_TOKEN
            chat_id = settings.TELEGRAM_CHAT_ID
            try:
                error_message = (
                    f"Error: [status code {response.status_code}]: {response.reason_phrase}\n"
                    f"Method {request.method} - URL: {request.path}\n"
                    f"User: {request.user}\n"
                    f"Content: {response.content.decode('utf-8')[:3000]}\n"
                )

                # Send the error message to the Telegram bot
                # Replace <chat_id> with the actual chat ID you want to send the message to
                requests.post(
                    f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage",
                    data={"chat_id": chat_id, "text": error_message[:4096]},
                    timeout=10,
                )
            except Exception as error:
                logger.warning("Error when try send alert to Telegram %s", error)

        process = multiprocessing.Process(target=send_message_in_process)
        process.start()
