# DDMPay UTM API

API Flask para gerar links curtos rastreaveis, redirecionar para o DDMPay e consolidar metricas por canal/campanha.

## Endpoints

- `GET /utm` - gerador de links curtos.
- `GET /dashboard` - dashboard de cliques, acordos, pagamentos e funil.
- `GET /l/<token>` - link curto; redireciona para o DDMPay com `par1`, `par2`, `par3` e `tid`.
- `POST /api/funil-evento` - recebe eventos de etapa do DDMPay.
- `GET /api/metricas` - dados do dashboard.
- `GET /health` - health check.

## Link curto

O gerador cria links neste formato:

```text
https://seudominio.com/l/eyJpIjoi...
```

Ao clicar, a API redireciona para:

```text
https://ddmpay.ddmacordos.com/acesso/?par1=CPF&par2=canal&par3=campanha&tid=ID_DO_RASTREIO
```

No gerador, o usuario ve os dois valores: a URL curta para disparo e o destino final no DDMPay.

## Funil detalhado

Para mostrar onde o cliente parou, o DDMPay precisa chamar `POST /api/funil-evento` em cada etapa.

Exemplo de payload:

```json
{
  "tid": "id_do_link",
  "par1": "cpf_ou_matricula",
  "par2": "whatsapp",
  "par3": "campanha_lote",
  "etapa": "cpf_view",
  "url": "https://ddmpay.ddmacordos.com/acesso/"
}
```

Etapas aceitas:

- `click` - cliente clicou no link curto.
- `cpf_view` - chegou na tela do CPF.
- `cpf_submit` - informou o CPF.
- `payment_view` - chegou na tela de pagamento.
- `payment_start` - iniciou o pagamento.
- `paid` - pagou.

Antes de ativar o funil detalhado, rode `criar_tabela_funil_eventos.sql` no MySQL e garanta `INSERT` para o usuario da aplicacao.

## Rodar localmente

```bash
pip install -r requirements.txt
python app.py
```

## Variaveis de ambiente

- `MYSQL_HOST`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`
- `MYSQL_PORT`
- `DDMPAY_CHECKOUT_URL`
