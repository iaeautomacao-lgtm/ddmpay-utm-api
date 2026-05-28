from flask import Flask, request, redirect
import mysql.connector
from datetime import datetime
import os

app = Flask(__name__)

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
    return mysql.connector.connect(**DB_CONFIG)


@app.route('/acesso', methods=['GET'])
def acesso():
    """
    Captura parâmetros UTM, salva no banco e redireciona para checkout
    URL: /acesso/?par1=aaaa&par2=bbbb&par3=cc
    """
    try:
        # Captura parâmetros da URL
        par1 = request.args.get('par1', '')
        par2 = request.args.get('par2', '')
        par3 = request.args.get('par3', '')
        
        # Captura dados de contexto
        ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        url_full = request.url
        
        # Conecta ao banco e insere
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = """
        INSERT INTO links_ddmpay (data_hora, url, ip, user_agent, par1, par2, par3)
        VALUES (NOW(), %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(sql, (url_full, ip, user_agent, par1, par2, par3))
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Registro inserido: par1={par1}, par2={par2}, par3={par3}, ip={ip}")
        
    except Exception as e:
        print(f"❌ Erro ao inserir no banco: {e}")
    
    # Redireciona para checkout (com ou sem sucesso de gravação)
    return redirect(CHECKOUT_URL)


@app.route('/health', methods=['GET'])
def health():
    """Health check para Vercel"""
    return {'status': 'ok'}, 200


if __name__ == '__main__':
    # Para desenvolvimento local
    app.run(debug=True, port=5000)
