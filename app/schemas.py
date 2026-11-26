from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field, field_validator


CategoriaMensagem = Literal["duvida", "reclamacao", "solicitacao", "outro"]
PrioridadeMensagem = Literal["baixa", "media", "alta", "urgente"]
SetorSugerido = Literal[
    "suporte_tecnico",
    "atendimento_cliente",
    "financeiro",
    "operacoes",
    "qualidade",
]


class MensagemEntrada(BaseModel):
    mensagem: str = Field(
        ...,
        min_length=3,
        max_length=4000,
        description="Texto original enviado pelo cliente.",
    )
    remetente: str | None = Field(
        default=None,
        max_length=160,
        description="Nome, telefone, e-mail ou identificador do cliente.",
    )
    canal: str | None = Field(
        default="whatsapp",
        max_length=60,
        description="Canal de origem da mensagem.",
    )
    metadata: dict[str, str | int | float | bool | None] = Field(
        default_factory=dict,
        description="Metadados adicionais enviados pela automacao.",
    )

    @field_validator("mensagem")
    @classmethod
    def validar_mensagem_nao_vazia(cls, valor: str) -> str:
        limpo = valor.strip()
        if not limpo:
            raise ValueError("A mensagem nao pode conter apenas espacos em branco.")
        return limpo


class ClassificacaoLLM(BaseModel):
    categoria: CategoriaMensagem
    prioridade: PrioridadeMensagem
    setor_sugerido: SetorSugerido
    resumo: str = Field(..., min_length=5, max_length=240)
    intencao_detectada: str = Field(..., min_length=3, max_length=120)
    confianca: float = Field(..., ge=0.0, le=1.0)
    requer_resposta_imediata: bool = False
    resposta_sugerida: str = Field(..., min_length=5, max_length=500)


class ClassificacaoResposta(BaseModel):
    id_processamento: str
    processado_em: str
    origem_classificacao: Literal["llm", "fallback_regras"]
    canal: str
    remetente: str | None
    mensagem_original: str
    classificacao: ClassificacaoLLM

    @staticmethod
    def agora_iso() -> str:
        return datetime.now(timezone.utc).isoformat()