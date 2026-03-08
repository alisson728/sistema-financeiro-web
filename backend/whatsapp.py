from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import requests


@dataclass
class SendResult:
    ok: bool
    request_payload: dict[str, Any]
    response_body: str
    status_code: int


class WhatsAppError(Exception):
    pass


class MetaWhatsAppClient:
    def __init__(self, api_version: str, phone_number_id: str, access_token: str):
        self.api_version = api_version
        self.phone_number_id = phone_number_id
        self.access_token = access_token

    @property
    def endpoint(self) -> str:
        return f'https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages'

    def send_template_message(
        self,
        to_number: str,
        template_name: str,
        language_code: str,
        body_params: list[str],
    ) -> SendResult:
        payload: dict[str, Any] = {
            'messaging_product': 'whatsapp',
            'to': to_number,
            'type': 'template',
            'template': {
                'name': template_name,
                'language': {'code': language_code},
                'components': [
                    {
                        'type': 'body',
                        'parameters': [{'type': 'text', 'text': p} for p in body_params],
                    }
                ],
            },
        }
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }
        resp = requests.post(self.endpoint, json=payload, headers=headers, timeout=30)
        return SendResult(
            ok=200 <= resp.status_code < 300,
            request_payload=payload,
            response_body=resp.text,
            status_code=resp.status_code,
        )


def build_due_reminder_text(descricao: str, valor: float, data_vencimento: str) -> str:
    return f"Lembrete financeiro: '{descricao}' vence em {data_vencimento}. Valor: R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
