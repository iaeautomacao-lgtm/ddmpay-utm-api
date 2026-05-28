# DDMPay UTM API

API serverless em Python + Flask para capturar parâmetros UTM e redirecionar para checkout.

## 🚀 Deploy

1. Conectar repo ao Vercel
2. Deploy automático

## 🔗 Endpoints

- `GET /api/acesso?par1=XXX&par2=YYY&par3=ZZZ` - Captura UTM e redireciona
- `GET /api/health` - Health check

## 📝 Exemplo

```
https://seu-app.vercel.app/api/acesso?par1=aaaa&par2=bbbb&par3=cc
↓
Salva em: links_ddmpay
Redireciona para: https://ddmpay.ddmacordos.com/acesso/
```

## 🔑 Variáveis

- Senha MySQL em `api/acesso.py`
