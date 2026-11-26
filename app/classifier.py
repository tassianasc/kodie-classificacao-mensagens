import json
import logging
import re
from typing import Literal
import httpx
from app.config import settings
from app.fallback import classificar_por_regras
from app.prompts import SYSTEM_PROMPT, montar_prompt_usuario
from app.schemas import ClassificacaoLLM

logger = logging.getLogger("kodie.classifier")


def _extrair_json_bruto(conteudo: str) -> dict:
    limpo = conteudo.strip()
    bloco_markdown = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", limpo, flags=re.DOTALL)
    if bloco_markdown:
        limpo = bloco_markdown.group(1)
    else:
        inicio = limpo.find("{")
        fim = limpo.rfind("}")
        if inicio != -1 and fim != -1 and fim > inicio:
            limpo = limpo[inicio : fim + 1]
    return json.loads(limpo)


async def classificar_mensagem(
    mensagem: str,
    canal: str | None = None,
    remetente: str | None = None,
) -> tuple[ClassificacaoLLM, Literal["llm", "fallback_regras"]]:
    if not settings.gemini_api_key.strip() or settings.gemini_api_key.strip() == "sua_chave_gemini_aqui":
        logger.warning("GEMINI_API_KEY nao configurada; utilizando fallback deterministico por regras.")
        return classificar_por_regras(mensagem), "fallback_regras"

    url = f"{settings.gemini_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.gemini_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.gemini_model,
        "temperature": settings.llm_temperature,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": montar_prompt_usuario(mensagem, canal, remetente)},
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            body = response.json()

        conteudo = body["choices"][0]["message"]["content"]
        dados_json = _extrair_json_bruto(conteudo)
        resultado = ClassificacaoLLM.model_validate(dados_json)
        return resultado, "llm"

    except (httpx.HTTPError, KeyError, IndexError, json.JSONDecodeError, ValueError) as exc:
        logger.error("Falha na classificacao via LLM (%s); acionando fallback por regras.", exc)
        return classificar_por_regras(mensagem), "fallback_regras"