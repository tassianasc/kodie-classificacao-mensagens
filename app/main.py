import logging
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from app.classifier import classificar_mensagem
from app.config import settings
from app.schemas import ClassificacaoResposta, MensagemEntrada

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("kodie.api")

app = FastAPI(
    title="KODIE - API de Classificacao de Mensagens",
    description="API para triagem, classificacao estruturada com IA e roteamento de mensagens de clientes.",
    version="1.0.0",
)


@app.exception_handler(Exception)
async def erro_inesperado_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Erro interno nao tratado em %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno ao processar a solicitacao."},
    )


@app.get("/health", tags=["Saude"])
async def healthcheck() -> dict[str, str]:
    chave_valida = bool(
        settings.gemini_api_key.strip()
        and settings.gemini_api_key.strip() != "sua_chave_gemini_aqui"
    )
    return {
        "status": "ok",
        "ambiente": settings.app_env,
        "modelo_llm": settings.gemini_model,
        "llm_configurada": str(chave_valida).lower(),
    }


@app.post(
    "/api/v1/mensagens/classificar",
    response_model=ClassificacaoResposta,
    status_code=200,
    tags=["Classificacao"],
)
async def endpoint_classificar_mensagem(payload: MensagemEntrada) -> ClassificacaoResposta:
    id_processamento = str(uuid.uuid4())
    logger.info(
        "Recebida mensagem id=%s canal=%s remetente=%s",
        id_processamento,
        payload.canal,
        payload.remetente or "anonimo",
    )

    try:
        classificacao, origem = await classificar_mensagem(
            mensagem=payload.mensagem,
            canal=payload.canal,
            remetente=payload.remetente,
        )
    except Exception as exc:
        logger.exception("Falha critica ao classificar mensagem id=%s: %s", id_processamento, exc)
        raise HTTPException(status_code=502, detail="Falha ao processar classificacao da mensagem.") from exc

    resposta = ClassificacaoResposta(
        id_processamento=id_processamento,
        processado_em=ClassificacaoResposta.agora_iso(),
        origem_classificacao=origem,
        canal=payload.canal or "nao_informado",
        remetente=payload.remetente,
        mensagem_original=payload.mensagem,
        classificacao=classificacao,
    )

    logger.info(
        "Mensagem classificada id=%s origem=%s categoria=%s prioridade=%s setor=%s",
        id_processamento,
        origem,
        classificacao.categoria,
        classificacao.prioridade,
        classificacao.setor_sugerido,
    )
    return resposta