from flask import Flask, request, redirect, jsonify
from urllib.parse import urlencode
import json
import os
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# ============================================================================
# CONFIGURAÇÃO SEGURA DO BANCO (usa variáveis de ambiente)
# ============================================================================
MYSQL_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', '162.214.155.190'),
    'user': os.environ.get('MYSQL_USER', 'ddm_ia'),
    'password': os.environ.get('MYSQL_PASSWORD', 'o#G3AHP1O}dt'),
    'database': os.environ.get('MYSQL_DATABASE', 'ddm_ddmadv'),
    'port': int(os.environ.get('MYSQL_PORT', 3306))
}

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def get_db_connection():
    """Cria conexão segura com o banco"""
    try:
        cnx = mysql.connector.connect(**MYSQL_CONFIG)
        return cnx
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None


def extract_param_from_url(url, param_name):
    """Extrai parâmetro da URL de forma segura"""
    try:
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        return params.get(param_name, [None])[0]
    except:
        return None


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return json.dumps({'status': 'ok'}), 200, {'Content-Type': 'application/json'}


@app.route('/acesso', methods=['GET'])
def acesso():
    """
    Captura parâmetros UTM e redireciona para DDMPay
    URL: /acesso/?par1=aaaa&par2=bbbb&par3=cc
    """
    params = request.args.to_dict()
    
    if params:
        checkout_url = 'https://ddmpay.ddmacordos.com/acesso/?' + urlencode(params)
    else:
        checkout_url = 'https://ddmpay.ddmacordos.com/acesso/'
    
    print(f"[ACESSO] Redirecionando para: {checkout_url}")
    return redirect(checkout_url)


@app.route('/webhook/pagamento', methods=['POST'])
def webhook_pagamento():
    """Recebe confirmação de pagamento do DDMPay"""
    try:
        data = request.get_json()
        
        print(f"[WEBHOOK] Pagamento recebido:")
        print(f"  Cliente: {data.get('cliente_id')}")
        print(f"  Valor: R$ {data.get('valor')}")
        print(f"  Status: {data.get('status')}")
        
        return {
            'status': 'recebido',
            'mensagem': 'Pagamento processado'
        }, 200
        
    except Exception as e:
        print(f"[WEBHOOK] Erro: {e}")
        return {'status': 'erro', 'mensagem': str(e)}, 400


@app.route('/api/metricas', methods=['GET'])
def api_metricas():
    """
    Endpoint de métricas - retorna dados REAIS do banco
    Query params:
      - data_inicio: YYYY-MM-DD (default: últimos 30 dias)
      - data_fim: YYYY-MM-DD (default: hoje)
      - canal: sms|whatsapp|email|rcs (default: todos)
    
    Retorna JSON com:
      - total_cliques
      - por_canal
      - tendencia_ultimos_7_dias
    """
    try:
        # Parâmetros da query
        data_fim = request.args.get('data_fim', datetime.now().strftime('%Y-%m-%d'))
        dias = int(request.args.get('dias', 30))
        data_inicio = request.args.get('data_inicio', 
            (datetime.strptime(data_fim, '%Y-%m-%d') - timedelta(days=dias)).strftime('%Y-%m-%d'))
        
        canal_filtro = request.args.get('canal', 'todos').lower()
        
        # Conectar ao banco
        cnx = get_db_connection()
        if not cnx:
            return {'error': 'Conexão com banco falhou'}, 500
        
        cursor = cnx.cursor(dictionary=True)
        
        # QUERY 1: Total de cliques no período
        query_total = """
            SELECT COUNT(*) as total FROM ddm_ddmadv.links_ddmpay
            WHERE DATE(data_hora) BETWEEN %s AND %s
        """
        cursor.execute(query_total, (data_inicio, data_fim))
        total_cliques = cursor.fetchone()['total']
        
        # QUERY 2: Cliques por canal (par2)
        query_canais = """
            SELECT 
                CASE 
                    WHEN url LIKE '%par2=sms%' THEN 'SMS'
                    WHEN url LIKE '%par2=whatsapp%' THEN 'WhatsApp'
                    WHEN url LIKE '%par2=email%' THEN 'Email'
                    WHEN url LIKE '%par2=rcs%' THEN 'RCS'
                    ELSE 'Sem Canal'
                END as canal,
                COUNT(*) as cliques
            FROM ddm_ddmadv.links_ddmpay
            WHERE DATE(data_hora) BETWEEN %s AND %s
            GROUP BY canal
            ORDER BY cliques DESC
        """
        cursor.execute(query_canais, (data_inicio, data_fim))
        por_canal = {row['canal']: row['cliques'] for row in cursor.fetchall()}
        
        # QUERY 3: Tendência últimos 7 dias
        query_tendencia = """
            SELECT 
                DATE(data_hora) as data,
                COUNT(*) as cliques,
                CASE 
                    WHEN url LIKE '%par2=sms%' THEN 'SMS'
                    WHEN url LIKE '%par2=whatsapp%' THEN 'WhatsApp'
                    WHEN url LIKE '%par2=email%' THEN 'Email'
                    WHEN url LIKE '%par2=rcs%' THEN 'RCS'
                    ELSE 'Sem Canal'
                END as canal
            FROM ddm_ddmadv.links_ddmpay
            WHERE data_hora >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(data_hora), canal
            ORDER BY data DESC
        """
        cursor.execute(query_tendencia)
        tendencia = cursor.fetchall()
        
        cursor.close()
        cnx.close()
        
        # Formatar resposta
        resposta = {
            'periodo': {
                'data_inicio': data_inicio,
                'data_fim': data_fim,
                'dias': dias
            },
            'metricas': {
                'total_cliques': total_cliques,
                'por_canal': por_canal,
                'tendencia_ultimos_7_dias': [
                    {
                        'data': str(row['data']),
                        'cliques': row['cliques'],
                        'canal': row['canal']
                    }
                    for row in tendencia
                ]
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(resposta), 200
        
    except Exception as e:
        print(f"[API METRICAS] Erro: {e}")
        return {'error': str(e)}, 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
