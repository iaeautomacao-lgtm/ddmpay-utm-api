# API UTM para CRM

Use esta API para criar um link unico por campanha. O CRM deve gerar o link antes do disparo e usar o `link_campanha` na mensagem.

Todas as chamadas do CRM devem enviar:

```http
X-API-Key: sua_chave_secreta
Content-Type: application/json
```

Configure a chave no servidor em `.env`:

```env
UTM_API_KEY=sua_chave_secreta
```

## Criar campanha

```http
POST https://utmpay.grupoddm.ia.br/api/criar-campanha
```

```json
{
  "sistema": "ddm",
  "canal": "sms",
  "campanha": "cobranca_setembro_lote1",
  "url_destino": "https://ddmpay.ddmacordos.com/acesso/",
  "janela_minutos": 30
}
```

Resposta:

```json
{
  "status": "ok",
  "codigo": "abc123",
  "tid": "mtabc123",
  "sistema": "ddm",
  "canal": "sms",
  "campanha": "cobranca_setembro_lote1",
  "link_campanha": "https://utmpay.grupoddm.ia.br/c/abc123",
  "url_destino_final": "https://ddmpay.ddmacordos.com/acesso/?sistema=ddm&canal=sms&campanha=cobranca_setembro_lote1&tid=mtabc123&utm_source=ddm&utm_medium=sms&utm_campaign=cobranca_setembro_lote1"
}
```

O CRM deve enviar na mensagem somente o campo `link_campanha`.

## Como o rastreamento funciona

Quando o aluno clica em `link_campanha`, nosso sistema registra:

- campanha;
- sistema/instituicao;
- canal;
- data e hora do clique;
- visitante unico aproximado.

Depois disso, o dashboard cruza os cliques com os registros do banco `IA_acessos` dentro da janela configurada, normalmente 30 minutos. Assim a ferramenta mostra por campanha:

- total de cliques;
- visitantes unicos;
- alunos identificados no sistema;
- alunos que pesquisaram CPF;
- alunos que visualizaram simulacao/acordo;
- alunos que iniciaram acordo.

## Sistemas aceitos

- `ddm`
- `cruzeirodosul`
- `yduqs`
- `anima`
- `anima2`
- `ubec`
- `neon`
- `avenida`
- `datora`
- `vero`
- `vero2`
- `verob2b`
- `fiergs`
- `fumec`

Light e SESI/SENAI nao entram nesse rastreamento.

## Observacao

As APIs antigas `/api/gerar-link` e `/api/gerar-links-lote` continuam existindo para casos em que o CRM consiga enviar links individuais por aluno. Para campanhas com um link unico, use `/api/criar-campanha`.
