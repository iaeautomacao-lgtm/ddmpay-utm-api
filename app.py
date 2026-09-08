from flask import Flask, request, redirect, jsonify, send_file
from urllib.parse import urlencode
import json
import os
import base64
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

CHECKOUT_URL = os.environ.get('DDMPAY_CHECKOUT_URL', 'https://ddmpay.ddmacordos.com/acesso/')
FUNIL_ETAPAS = {
    'click': 'Clicou no link',
    'cpf_view': 'Chegou na tela do CPF',
    'cpf_submit': 'Informou o CPF',
    'payment_view': 'Chegou no pagamento',
    'payment_start': 'Iniciou pagamento',
    'paid': 'Pagou',
}

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


def decode_short_token(token):
    """Decodifica token curto gerado no front: base64url(JSON compacto)."""
    try:
        padded = token + ('=' * (-len(token) % 4))
        raw = base64.urlsafe_b64decode(padded.encode('ascii')).decode('utf-8')
        data = json.loads(raw)
        if isinstance(data, list):
            data = {
                'i': data[0] if len(data) > 0 else '',
                'c': data[1] if len(data) > 1 else '',
                'm': data[2] if len(data) > 2 else '',
                't': data[3] if len(data) > 3 else '',
            }
        return {
            'par1': str(data.get('i', '')).strip(),
            'par2': str(data.get('c', '')).strip().lower(),
            'par3': str(data.get('m', '')).strip(),
            'tid': str(data.get('t', '')).strip(),
        }
    except Exception as e:
        print(f"[LINK CURTO] token invalido: {e}")
        return None


def ddmpay_url_from_params(params):
    clean = {k: v for k, v in params.items() if v}
    if clean:
        return CHECKOUT_URL + '?' + urlencode(clean)
    return CHECKOUT_URL


def salvar_evento_funil(tid, par1, par2, par3, etapa, pagina_url='', metadata=None):
    cnx = get_db_connection()
    if not cnx:
        return False

    cursor = cnx.cursor()
    cursor.execute("""
        INSERT INTO ddm_ddmadv.ddmpay_funil_eventos
            (tid, par1, par2, par3, etapa, etapa_label, pagina_url, metadata, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
    """, (
        tid or None,
        par1 or None,
        par2 or None,
        par3 or None,
        etapa,
        FUNIL_ETAPAS[etapa],
        pagina_url or None,
        json.dumps(metadata or {}, ensure_ascii=False),
    ))
    cnx.commit()
    cursor.close()
    cnx.close()
    return True


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.route('/')
def root():
    return redirect('/dashboard')


@app.route('/dashboard')
def dashboard():
    return send_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dashboard.html'))


@app.route('/utm')
def utm():
    return send_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'utm.html'))


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
    checkout_url = ddmpay_url_from_params(params)
    
    print(f"[ACESSO] Redirecionando para: {checkout_url}")
    return redirect(checkout_url)


@app.route('/l/<token>', methods=['GET'])
def link_curto(token):
    """
    Redireciona link curto para o DDMPay.
    Exemplo: /l/<token> -> https://ddmpay.ddmacordos.com/acesso/?par1=...&par2=...&par3=...&tid=...
    """
    data = decode_short_token(token)
    if not data or not data.get('par1'):
        return jsonify({'status': 'erro', 'mensagem': 'Link invalido'}), 400

    params = {
        'par1': data.get('par1'),
        'par2': data.get('par2'),
        'par3': data.get('par3'),
        'tid': data.get('tid'),
    }
    checkout_url = ddmpay_url_from_params(params)
    try:
        salvar_evento_funil(data.get('tid'), data.get('par1'), data.get('par2'), data.get('par3'), 'click', checkout_url)
    except Exception as e:
        print(f"[LINK CURTO] clique nao salvo no funil: {e}")
    print(f"[LINK CURTO] tid={data.get('tid')} destino={checkout_url}")
    return redirect(checkout_url)


@app.route('/api/funil-evento', methods=['POST'])
def api_funil_evento():
    """
    Recebe eventos de etapa do DDMPay para rastrear onde o cliente parou.
    Body JSON: {tid, par1, par2, par3, etapa, url, metadata}
    """
    try:
        data = request.get_json(force=True) or {}
        etapa = str(data.get('etapa', '')).strip().lower()
        if etapa not in FUNIL_ETAPAS:
            return jsonify({'status': 'erro', 'mensagem': 'Etapa invalida'}), 400

        tid = str(data.get('tid', '')).strip()
        par1 = str(data.get('par1', '')).strip()
        par2 = str(data.get('par2', '')).strip().lower()
        par3 = str(data.get('par3', '')).strip()
        pagina_url = str(data.get('url', '')).strip()
        metadata = data.get('metadata') or {}
        if not salvar_evento_funil(tid, par1, par2, par3, etapa, pagina_url, metadata):
            return jsonify({'status': 'erro', 'mensagem': 'Conexao com banco falhou'}), 500

        return jsonify({'status': 'recebido', 'etapa': etapa, 'etapa_label': FUNIL_ETAPAS[etapa]}), 200
    except Exception as e:
        print(f"[FUNIL EVENTO] Erro: {e}")
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@app.route('/webhook/pagamento', methods=['POST'])
def webhook_pagamento():
    """Recebe confirmação de pagamento do DDMPay"""
    try:
        data = request.get_json(force=True) or {}

        cliente_id = data.get('cliente_id', 'desconhecido')
        valor = float(data.get('valor', 0))
        status = data.get('status', 'pendente')
        canal = data.get('canal', '')
        campanha = data.get('campanha', '')

        print(f"[WEBHOOK] cliente={cliente_id} valor=R${valor} status={status} canal={canal} campanha={campanha}")

        cnx = get_db_connection()
        if cnx:
            try:
                cursor = cnx.cursor()
                cursor.execute("""
                    INSERT INTO ddm_ddmadv.conversoes
                        (cliente_id, valor, status, canal, campanha, data_pagamento)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """, (cliente_id, valor, status, canal, campanha))
                cnx.commit()
                cursor.close()
                cnx.close()
                print(f"[WEBHOOK] Salvo em conversoes.")
            except Exception as db_err:
                print(f"[WEBHOOK] Nao foi possivel salvar (tabela existe?): {db_err}")
        else:
            print("[WEBHOOK] Sem conexao com banco.")

        return jsonify({'status': 'recebido', 'cliente_id': cliente_id}), 200

    except Exception as e:
        print(f"[WEBHOOK] Erro: {e}")
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 400


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
        
        # QUERY 1: Total de cliques no período + clientes únicos
        query_total = """
            SELECT
                COUNT(*) as total,
                COUNT(DISTINCT SUBSTRING_INDEX(SUBSTRING_INDEX(url, 'par1=', -1), '&', 1)) as total_unicos
            FROM ddm_ddmadv.links_ddmpay
            WHERE DATE(data_hora) BETWEEN %s AND %s
            AND url LIKE '%par1=%'
        """
        cursor.execute(query_total, (data_inicio, data_fim))
        row_total = cursor.fetchone()
        total_cliques = row_total['total']
        total_cliques_unicos = row_total['total_unicos']
        
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
              AND url LIKE '%par1=%'
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
              AND url LIKE '%par1=%'
            GROUP BY DATE(data_hora), canal
            ORDER BY data DESC
        """
        cursor.execute(query_tendencia)
        tendencia = cursor.fetchall()

        # QUERY 4: Funil + pagamento via VIEW vw_ddmpay_completo
        # grain = (clique, acordo); pagamento (valor_pago) agregado por acordo na view.
        # "pago" = valor_pago > 0 (vem de acordos_pagamentos.valor_pago / baixa_local).
        total_acordos = 0      # usuarios distintos com acordo
        total_pagaram = 0      # usuarios distintos que pagaram
        valor_total = 0.0      # R$ pago (dedup por acordo)
        ticket_medio = 0.0
        volume_por_canal = {}  # R$ pago por canal
        acordos_por_canal = {} # usuarios com acordo por canal
        por_canal_detalhe = {} # {canal: {cliques, usuarios, com_acordo, pagaram, valor_pago}}
        por_campanha = {}      # {campanha(par3): idem}
        funil_por_campanha = {}
        abandono_por_campanha = {}
        ultimos_acordos = []

        CANAL_LABEL = {'sms': 'SMS', 'whatsapp': 'WhatsApp', 'email': 'E-mail', 'rcs': 'RCS'}
        def label_canal(c):
            return CANAL_LABEL.get((c or '').strip().lower(), 'Outro')

        try:
            cursor.execute("""
                SELECT clique_id, clique_data, par1, canal, lote, nome,
                       nr_acordo, acordo_data, tem_acordo, valor_pago, pago
                FROM ddm_ddmadv.vw_ddmpay_completo
                WHERE DATE(clique_data) BETWEEN %s AND %s
            """, (data_inicio, data_fim))
            rows = cursor.fetchall()

            def novo():
                return {'cliques': set(), 'usuarios': set(), 'com_acordo': set(),
                        'pagaram': set(), 'acordos_pagos': {}}
            agg_canal, agg_camp = {}, {}
            users_acordo, users_pago, acordos_valor = set(), set(), {}

            for r in rows:
                par1 = r['par1']
                chaves = ((label_canal(r['canal']), agg_canal),
                          (((r['lote'] or '').strip() or '(sem campanha)'), agg_camp))
                for key, store in chaves:
                    b = store.setdefault(key, novo())
                    b['cliques'].add(r['clique_id'])
                    if par1:
                        b['usuarios'].add(par1)
                    if r['tem_acordo'] and par1:
                        b['com_acordo'].add(par1)
                    if r['pago']:
                        if par1:
                            b['pagaram'].add(par1)
                        if r['nr_acordo'] is not None:
                            b['acordos_pagos'][r['nr_acordo']] = float(r['valor_pago'] or 0)
                if r['tem_acordo'] and par1:
                    users_acordo.add(par1)
                if r['pago']:
                    if par1:
                        users_pago.add(par1)
                    if r['nr_acordo'] is not None:
                        acordos_valor[r['nr_acordo']] = float(r['valor_pago'] or 0)

            total_acordos = len(users_acordo)
            total_pagaram = len(users_pago)
            valor_total = round(sum(acordos_valor.values()), 2)
            ticket_medio = round(valor_total / total_pagaram, 2) if total_pagaram else 0.0

            def finalize(store):
                return {k: {
                    'cliques': len(b['cliques']),
                    'usuarios': len(b['usuarios']),
                    'com_acordo': len(b['com_acordo']),
                    'pagaram': len(b['pagaram']),
                    'valor_pago': round(sum(b['acordos_pagos'].values()), 2),
                } for k, b in store.items()}
            por_canal_detalhe = finalize(agg_canal)
            por_campanha = finalize(agg_camp)
            acordos_por_canal = {k: v['com_acordo'] for k, v in por_canal_detalhe.items()}
            volume_por_canal = {k: v['valor_pago'] for k, v in por_canal_detalhe.items()}

            # Ultimos acordos (1 linha por acordo, mais recentes)
            vistos = set()
            for r in sorted((x for x in rows if x['tem_acordo']),
                            key=lambda x: (x['acordo_data'] or datetime.min), reverse=True):
                if r['nr_acordo'] in vistos:
                    continue
                vistos.add(r['nr_acordo'])
                ultimos_acordos.append({
                    'aluno_id': r['par1'],
                    'nome': r['nome'] or '',
                    'canal': (r['canal'] or '').lower(),
                    'campanha': (r['lote'] or ''),
                    'valor': float(r['valor_pago'] or 0),
                    'status': 'pago' if r['pago'] else 'pendente',
                    'data': str(r['acordo_data']) if r['acordo_data'] else ''
                })
                if len(ultimos_acordos) >= 20:
                    break
        except Exception as e:
            print(f"[VIEW completo] erro: {e}")

        # Eventos finos do DDMPay: permitem saber a ultima tela atingida.
        # A tabela e alimentada pelo endpoint /api/funil-evento.
        try:
            cursor.execute("""
                SELECT tid, par1, par2, par3, etapa, etapa_label, pagina_url, created_at
                FROM ddm_ddmadv.ddmpay_funil_eventos
                WHERE DATE(created_at) BETWEEN %s AND %s
                ORDER BY created_at ASC
            """, (data_inicio, data_fim))
            event_rows = cursor.fetchall()

            ordem_etapas = {
                'click': 1,
                'cpf_view': 2,
                'cpf_submit': 3,
                'payment_view': 4,
                'payment_start': 5,
                'paid': 6,
            }

            def key_evento(ev):
                return ev.get('tid') or ev.get('par1') or ''

            campanhas_eventos = {}
            ultimos_por_cliente = {}

            for ev in event_rows:
                campanha = (ev.get('par3') or '').strip() or '(sem campanha)'
                cliente_key = key_evento(ev)
                if not cliente_key:
                    continue

                camp = campanhas_eventos.setdefault(campanha, {})
                etapa = ev.get('etapa')
                etapa_bucket = camp.setdefault(etapa, set())
                etapa_bucket.add(cliente_key)

                atual = ultimos_por_cliente.get((campanha, cliente_key))
                if (
                    atual is None
                    or ordem_etapas.get(etapa, 0) > ordem_etapas.get(atual.get('etapa'), 0)
                    or ev.get('created_at') > atual.get('created_at')
                ):
                    ultimos_por_cliente[(campanha, cliente_key)] = ev

            for campanha, etapas in campanhas_eventos.items():
                funil_por_campanha[campanha] = {
                    etapa: len(clientes)
                    for etapa, clientes in etapas.items()
                }

            for (campanha, _cliente_key), ev in ultimos_por_cliente.items():
                bucket = abandono_por_campanha.setdefault(campanha, {})
                etapa = ev.get('etapa') or 'desconhecido'
                item = bucket.setdefault(etapa, {
                    'etapa_label': ev.get('etapa_label') or FUNIL_ETAPAS.get(etapa, etapa),
                    'clientes': 0,
                    'ultima_url': ev.get('pagina_url') or '',
                })
                item['clientes'] += 1
        except Exception as e:
            print(f"[FUNIL EVENTOS] tabela indisponivel ou erro: {e}")

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
                'total_cliques_unicos': total_cliques_unicos,
                'por_canal': por_canal,
                'acordos_por_canal': acordos_por_canal,
                'volume_por_canal': volume_por_canal,
                'por_canal_detalhe': por_canal_detalhe,
                'por_campanha': por_campanha,
                'funil_por_campanha': funil_por_campanha,
                'abandono_por_campanha': abandono_por_campanha,
                'total_acordos': total_acordos,
                'total_pagaram': total_pagaram,
                'valor_total': valor_total,
                'ticket_medio': ticket_medio,
                'acordos': ultimos_acordos,
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
