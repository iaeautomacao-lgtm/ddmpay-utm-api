# Integracao do funil no DDMPay

Para o dashboard mostrar onde o cliente parou, o DDMPay precisa enviar eventos para esta API em cada etapa importante.

## 1. Criar tabela

Rode no MySQL:

```sql
SOURCE criar_tabela_funil_eventos.sql;
```

Se o usuario da aplicacao ainda nao tiver permissao de escrita nessa tabela, rode com usuario admin:

```sql
GRANT SELECT, INSERT ON ddm_ddmadv.ddmpay_funil_eventos TO '<MYSQL_USER>'@'%';
```

## 2. Preservar parametros

O link curto redireciona para o DDMPay assim:

```text
https://ddmpay.ddmacordos.com/acesso/?par1=CPF&par2=canal&par3=campanha&tid=ID_DO_RASTREIO
```

O DDMPay deve manter `tid`, `par1`, `par2` e `par3` durante o fluxo, ou pelo menos deixa-los disponiveis no JavaScript das paginas.

## 3. Enviar evento por etapa

Exemplo JavaScript:

```html
<script>
  function getParam(name) {
    return new URLSearchParams(window.location.search).get(name) || '';
  }

  function enviarEventoFunil(etapa, metadata) {
    return fetch('https://SEU-DOMINIO-DA-API.com/api/funil-evento', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tid: getParam('tid'),
        par1: getParam('par1'),
        par2: getParam('par2'),
        par3: getParam('par3'),
        etapa: etapa,
        url: window.location.href,
        metadata: metadata || {}
      })
    }).catch(function () {});
  }
</script>
```

## 4. Onde chamar

- Ao carregar a tela do CPF: `enviarEventoFunil('cpf_view')`
- Depois que o cliente informou o CPF com sucesso: `enviarEventoFunil('cpf_submit')`
- Ao carregar a tela de pagamento: `enviarEventoFunil('payment_view')`
- Quando ele clicar em pagar/gerar PIX/cartao/boleto: `enviarEventoFunil('payment_start')`
- Quando o pagamento for confirmado: `enviarEventoFunil('paid')`

A etapa `click` ja e registrada pela API quando o cliente acessa o link curto `/l/<token>`.
