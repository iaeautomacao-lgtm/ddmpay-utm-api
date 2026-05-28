"""
Vercel Serverless Function para capturar parâmetros UTM
GET /api/acesso?par1=XXX&par2=YYY&par3=ZZZ
"""

from flask import Flask, request, redirect
import mysql.connector
import json

# Configurações do banco de dados
DB_CONFIG = {
    'host': '162.214.155.190',
    'user': 'ddm_ia',
    'password': 'o#G3AHP1O}dt',
    'database': 'ddm_ddmadv',
    'port': 3306
}

# URL de redirecionamento
CHECKOUT_URL = 'https://ddmpay.ddmacordos.com/acesso/'


def get_db_connection():
    """Cria conexão com MySQL"""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        print(f"❌ Erro ao conectar no banco: {e}")
        return None


app = Flask(__name__)


@app.route('/api/acesso', methods=['GET'])
def acesso():
    """
    Captura parâmetros UTM, salva no banco e redireciona para checkout
    URL: /api/acesso?par1=aaaa&par2=bbbb&par3=cc
    """
    try:
        # Captura parâmetros da URL
        par1 = request.args.get('par1', '')
        par2 = request.args.get('par2', '')
        par3 = request.args.get('par3', '')
        
        # Captura dados de contexto
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        url_full = request.url
        
        print(f"📨 Recebido: par1={par1}, par2={par2}, par3={par3}, ip={ip}")
        
        # Conecta ao banco e insere
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            sql = """
            INSERT INTO links_ddmpay (data_hora, url, ip, user_agent, par1, par2, par3)
            VALUES (NOW(), %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(sql, (url_full, ip, user_agent, par1, par2, par3))
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"✅ Registro inserido com sucesso")
        
    except Exception as e:
        print(f"❌ Erro ao processar: {e}")
    
    # Redireciona para checkout (com ou sem sucesso de gravação)
    return redirect(CHECKOUT_URL)


@app.route('/api/health', methods=['GET'])
def health():
    """Health check para Vercel"""
    return json.dumps({'status': 'ok'}), 200, {'Content-Type': 'application/json'}


# Para Vercel
def handler(request):
    return app(request)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
