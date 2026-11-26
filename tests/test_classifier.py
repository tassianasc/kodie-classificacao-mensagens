from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_healthcheck():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_classificacao_reclamacao():
    response = client.post(
        "/api/v1/mensagens/classificar",
        json={
            "mensagem": "Minha fatura veio com cobranca indevida e o sistema nao funciona hoje.",
            "remetente": "Cliente Teste",
            "canal": "whatsapp",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["classificacao"]["categoria"] in ("reclamacao", "solicitacao", "duvida", "outro")
    assert body["classificacao"]["prioridade"] in ("baixa", "media", "alta", "urgente")
    assert len(body["classificacao"]["resumo"]) > 0


def test_classificacao_payload_invalido():
    response = client.post(
        "/api/v1/mensagens/classificar",
        json={"mensagem": "   "},
    )
    assert response.status_code == 422