import re
from app.schemas import (
    CategoriaMensagem,
    ClassificacaoLLM,
    PrioridadeMensagem,
    SetorSugerido,
)

_PALAVRAS_RECLAMACAO = (
    "reclamacao",
    "reclamar",
    "absurdo",
    "pessimo",
    "péssimo",
    "horrivel",
    "horrorível",
    "nao funciona",
    "não funciona",
    "quebrado",
    "estragado",
    "atraso",
    "atrasado",
    "cobrança indevida",
    "cobranca indevida",
    "cobraram duas vezes",
    "erro",
    "enganacao",
    "enganação",
    "procon",
)

_PALAVRAS_SOLICITACAO = (
    "quero",
    "preciso",
    "solicito",
    "solicitar",
    "cancelar",
    "cancelamento",
    "trocar",
    "troca",
    "segunda via",
    "2a via",
    "2ª via",
    "reembolso",
    "estorno",
    "atualizar",
    "alterar",
    "agendar",
    "emitir",
    "enviar",
    "nota fiscal",
)

_PALAVRAS_DUVIDA = (
    "como",
    "qual",
    "quais",
    "quando",
    "onde",
    "quanto",
    "funciona",
    "horario",
    "horário",
    "prazo",
    "duvida",
    "dúvida",
    "posso",
    "tem ",
    "?",
)

_PALAVRAS_URGENTE = (
    "urgente",
    "emergencia",
    "emergência",
    "parado",
    "fora do ar",
    "cobrança indevida",
    "cobranca indevida",
    "procon",
    "advogado",
)


def classificar_por_regras(mensagem: str) -> ClassificacaoLLM:
    texto = re.sub(r"\s+", " ", mensagem.lower()).strip()

    categoria: CategoriaMensagem = "outro"
    if any(termo in texto for termo in _PALAVRAS_RECLAMACAO):
        categoria = "reclamacao"
    elif any(termo in texto for termo in _PALAVRAS_SOLICITACAO):
        categoria = "solicitacao"
    elif any(termo in texto for termo in _PALAVRAS_DUVIDA):
        categoria = "duvida"

    prioridade: PrioridadeMensagem = "baixa"
    if any(termo in texto for termo in _PALAVRAS_URGENTE):
        prioridade = "urgente"
    elif categoria == "reclamacao":
        prioridade = "alta"
    elif categoria in ("duvida", "solicitacao"):
        prioridade = "media"

    setor: SetorSugerido = "atendimento_cliente"
    if any(p in texto for p in ("boleto", "fatura", "cobran", "pagamento", "reembolso", "estorno", "nota fiscal")):
        setor = "financeiro"
    elif any(p in texto for p in ("sistema", "app", "login", "senha", "erro", "bug", "nao funciona", "não funciona", "fora do ar")):
        setor = "suporte_tecnico"
    elif any(p in texto for p in ("entrega", "envio", "prazo", "agendar", "estoque", "pedido", "troca")):
        setor = "operacoes"
    elif categoria == "reclamacao":
        setor = "qualidade"

    palavras = mensagem.strip().split()
    resumo = " ".join(palavras[:22]) + ("..." if len(palavras) > 22 else "")
    requer_imediata = prioridade in ("alta", "urgente")

    intencoes = {
        "duvida": "Consulta de informacao",
        "reclamacao": "Registro de insatisfacao ou falha",
        "solicitacao": "Pedido de execucao ou alteracao",
        "outro": "Comunicacao geral",
    }

    respostas = {
        "duvida": "Recebemos sua duvida e ja encaminhamos para nossa equipe responder o quanto antes.",
        "reclamacao": "Lamentamos o ocorrido. Sua mensagem foi priorizada e encaminhada para o setor responsavel.",
        "solicitacao": "Recebemos sua solicitacao e ela foi direcionada para o setor responsavel pelo atendimento.",
        "outro": "Obrigado pela mensagem. Nossa equipe esta a disposicao para ajudar.",
    }

    return ClassificacaoLLM(
        categoria=categoria,
        prioridade=prioridade,
        setor_sugerido=setor,
        resumo=resumo,
        intencao_detectada=intencoes[categoria],
        confianca=0.62,
        requer_resposta_imediata=requer_imediata,
        resposta_sugerida=respostas[categoria],
    )