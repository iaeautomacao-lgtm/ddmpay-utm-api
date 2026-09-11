# API UTM para CRM

Use esta API para gerar links rastreáveis antes do disparo de campanhas.

Todas as chamadas devem enviar o header:

```http
X-API-Key: sua_chave_secreta
Content-Type: application/json
```

Configure a chave no servidor em `.env`:

```env
UTM_API_KEY=sua_chave_secreta
```

## Gerar um link

```http
POST https://utmpay.grupoddm.ia.br/api/gerar-link
```

```json
{
  "aluno_id": "12345678901",
  "canal": "sms",
  "campanha": "cobranca_setembro_lote1",
  "url_destino": "https://ddmpay.ddmacordos.com/acesso/"
}
```

Resposta:

```json
{
  "status": "ok",
  "aluno_id": "12345678901",
  "canal": "sms",
  "campanha": "cobranca_setembro_lote1",
  "tid": "mtabc123",
  "link_curto": "https://utmpay.grupoddm.ia.br/s/abc123",
  "url_destino_final": "https://ddmpay.ddmacordos.com/acesso/?par1=12345678901&par2=sms&par3=cobranca_setembro_lote1&tid=mtabc123"
}
```

O CRM deve usar `link_curto` na mensagem enviada ao aluno.

## Gerar links em lote

```http
POST https://utmpay.grupoddm.ia.br/api/gerar-links-lote
```

```json
{
  "canal": "whatsapp",
  "campanha": "cobranca_setembro_lote1",
  "url_destino": "https://ddmpay.ddmacordos.com/acesso/",
  "alunos": [
    "12345678901",
    "98765432100",
    {
      "aluno_id": "11122233344",
      "tid": "id_externo_opcional"
    }
  ]
}
```

Resposta:

```json
{
  "status": "ok",
  "total": 3,
  "links": [
    {
      "aluno_id": "12345678901",
      "link_curto": "https://utmpay.grupoddm.ia.br/s/abc123",
      "tid": "mtabc123"
    }
  ],
  "erros": []
}
```

Campos aceitos:

- `canal`: `sms`, `whatsapp`, `rcs` ou `email`.
- `campanha`: nome/lote da campanha.
- `url_destino`: opcional; se não enviar, usa `DDMPAY_CHECKOUT_URL`.
- `alunos`: lista de CPFs/IDs ou objetos com `aluno_id`.

Limite atual: 1000 alunos por chamada.
