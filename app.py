from flask import Flask, request, redirect
from urllib.parse import urlencode

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
    
    print(f"📨 Redirecionando para: {checkout_url}")
    
    # Redireciona para checkout com os parâmetros
    return redirect(checkout_url)


@app.route('/health', methods=['GET'])
def health():
    """Health check para Vercel"""
    return {'status': 'ok'}, 200


if __name__ == '__main__':
    # Para desenvolvimento local
    app.run(debug=True, port=5000)
