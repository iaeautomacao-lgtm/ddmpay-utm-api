from flask import Flask, request, redirect
from urllib.parse import urlencode
import json

app = Flask(__name__)

# URL base de redirecionamento
CHECKOUT_BASE_URL = 'https://ddmpay.ddmacordos.com/acesso/'


@app.route('/acesso', methods=['GET'])
def acesso():
    """
    Captura parâmetros UTM e redireciona para DDMPay com os parâmetros intactos
    URL: /acesso/?par1=aaaa&par2=bbbb&par3=cc
    
    DDMPay antigo já captura e salva automaticamente qualquer parâmetro após o ?
    """
    # Captura TODOS os parâmetros da URL
    params = request.args.to_dict()
    
    # Constrói URL de redirecionamento com os parâmetros
    if params:
        checkout_url = CHECKOUT_BASE_URL + '?' + urlencode(params)
    else:
        checkout_url = CHECKOUT_BASE_URL
    
    print(f"[ACESSO] Redirecionando para: {checkout_url}")
    
    # Redireciona para checkout com os parâmetros
    return redirect(checkout_url)


@app.route('/webhook/pagamento', methods=['POST'])
def webhook_pagamento():
    """
    Recebe confirmação de pagamento do DDMPay
    Body esperado:
    {
        "cliente_id": "12345678900",
        "valor": 500.00,
        "status": "pago"
    }
    """
    try:
        data = request.get_json()
        
        print(f"[WEBHOOK] Pagamento recebido:")
        print(f"  Cliente: {data.get('cliente_id')}")
        print(f"  Valor: R$ {data.get('valor')}")
        print(f"  Status: {data.get('status')}")
        
        # TODO: Integrar com n8n para processar dados
        
        return {
            'status': 'recebido',
            'mensagem': 'Pagamento processado'
        }, 200
        
    except Exception as e:
        print(f"[WEBHOOK] Erro: {e}")
        return {'status': 'erro', 'mensagem': str(e)}, 400


@app.route('/health', methods=['GET'])
def health():
    """Health check para Vercel"""
    return json.dumps({'status': 'ok'}), 200, {'Content-Type': 'application/json'}


if __name__ == '__main__':
    # Para desenvolvimento local
    app.run(debug=True, port=5000)
