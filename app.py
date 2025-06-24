# app.py - VERSÃO COMPLETA E AJUSTADA

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import bcrypt
import jwt
import datetime
import json
from functools import wraps
# from collections import defaultdict # Não está sendo usado, pode remover se quiser

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'sua_chave_secreta_agendamento_labs_uern_2025'
DATABASE = 'agendamento.db'

def get_db_connection():
    """Conecta ao banco SQLite e configura row_factory"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# VERSÃO AJUSTADA DA FUNÇÃO init_database()
def init_database():
    """Cria tabelas e insere dados iniciais se não existirem, com foco na robustez do admin"""
    conn = get_db_connection()
    
    # Verificar e adicionar colunas 'status' e 'tipo' na tabela professores se não existirem
    try:
        cursor = conn.execute("PRAGMA table_info(professores)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'status' not in columns:
            print("Adicionando coluna 'status' à tabela professores...")
            conn.execute('ALTER TABLE professores ADD COLUMN status TEXT DEFAULT "ativo"')
            # commit aqui é opcional se houver um commit maior no final da função, mas seguro
            conn.commit() 
            print("✅ Coluna 'status' adicionada com sucesso!")
        if 'tipo' not in columns:
            print("Adicionando coluna 'tipo' à tabela professores...")
            conn.execute('ALTER TABLE professores ADD COLUMN tipo TEXT DEFAULT "professor"')
            conn.commit()
            print("✅ Coluna 'tipo' adicionada com sucesso!")
    except sqlite3.OperationalError:
        # Tabela não existe, será criada abaixo
        print("INFO: Tabela 'professores' não existe ainda, será criada.")
        pass
    
    # Criação da tabela professores
    conn.execute('''
        CREATE TABLE IF NOT EXISTS professores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_completo TEXT NOT NULL,
            matricula TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE, 
            telefone TEXT,
            departamento TEXT,
            senha_hash TEXT NOT NULL,
            status TEXT DEFAULT 'ativo',
            tipo TEXT DEFAULT 'professor',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Criação da tabela laboratórios
    conn.execute('''
        CREATE TABLE IF NOT EXISTS laboratorios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            localizacao TEXT NOT NULL,
            capacidade INTEGER NOT NULL,
            recursos TEXT,
            status TEXT DEFAULT 'disponivel',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Criação da tabela reservas
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            professor_id INTEGER NOT NULL,
            laboratorio_id INTEGER NOT NULL,
            data DATE NOT NULL,
            horario_inicio TIME NOT NULL,
            horario_fim TIME NOT NULL,
            disciplina TEXT NOT NULL,
            turma TEXT NOT NULL,
            descricao_atividade TEXT,
            status TEXT DEFAULT 'confirmada', 
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (professor_id) REFERENCES professores (id) ON DELETE CASCADE,
            FOREIGN KEY (laboratorio_id) REFERENCES laboratorios (id) ON DELETE CASCADE
        )
    ''')
    conn.commit() # Commit após a criação das tabelas e alterações de schema

    # --- INÍCIO DA LÓGICA AJUSTADA PARA ADMIN E PROFESSORES INICIAIS ---
    
    # Verificar e garantir que o admin exista e esteja correto
    admin_row = conn.execute("SELECT id, tipo, status FROM professores WHERE matricula = '999999'").fetchone()
    senha_admin_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())

    if admin_row is None:
        print("INFO: Admin '999999' não encontrado. Criando novo admin.")
        conn.execute('''
            INSERT INTO professores (nome_completo, matricula, email, telefone, departamento, senha_hash, tipo, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('Admin Geral', '999999', 'admin@uern.br', '', 'Administração', senha_admin_hash, 'admin', 'ativo'))
    elif admin_row['tipo'] != 'admin' or admin_row['status'] != 'ativo':
        print("INFO: Admin '999999' encontrado, mas com tipo/status incorreto ou senha pode estar desatualizada. Atualizando.")
        conn.execute('''
            UPDATE professores SET tipo = 'admin', status = 'ativo', senha_hash = ? 
            WHERE matricula = '999999'
        ''', (senha_admin_hash,)) # Atualiza a senha também para garantir consistência
    else:
        print("INFO: Admin '999999' já existe e está correto.")
    conn.commit()

    # Lógica para outros professores iniciais
    # Insere apenas se a tabela tiver apenas o admin (ou estiver vazia antes do admin ser tratado)
    prof_count_outros = conn.execute("SELECT COUNT(*) as count FROM professores WHERE matricula != '999999'").fetchone()['count']
    
    if prof_count_outros == 0:
        print("INFO: Nenhum outro professor encontrado. Inserindo professores iniciais padrão.")
        senha_hash_prof = bcrypt.hashpw('123456'.encode('utf-8'), bcrypt.gensalt())
        professores_iniciais = [
            # (nome_completo, matricula, email, telefone, departamento, senha_hash, tipo, status)
            ('Prof. André Gustavo', '123456', 'andre@uern.br', '(84) 99999-9999', 'Ciência da Computação', senha_hash_prof, 'professor', 'ativo'),
            ('Prof. Maria Silva', '123457', 'maria@uern.br', '(84) 98888-8888', 'Ciência da Computação', senha_hash_prof, 'professor', 'ativo'),
        ]
        for prof_data in professores_iniciais:
            # Usar INSERT OR IGNORE para o caso de alguma matricula já existir por um motivo inesperado
            conn.execute('''
                INSERT OR IGNORE INTO professores 
                (nome_completo, matricula, email, telefone, departamento, senha_hash, tipo, status) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', prof_data)
        conn.commit()
    else:
        print(f"INFO: {prof_count_outros} outros professor(es) já existem. Não inserindo professores iniciais padrão.")

    # Atualizar status e tipo para professores existentes que não são o admin e podem ter valores NULL
    conn.execute("UPDATE professores SET status = 'ativo' WHERE status IS NULL AND matricula != '999999'")
    conn.execute("UPDATE professores SET tipo = 'professor' WHERE tipo IS NULL AND matricula != '999999'")
    conn.commit()

    # Verificar e inserir laboratórios iniciais
    existing_labs_row = conn.execute('SELECT COUNT(*) as count FROM laboratorios').fetchone()
    if existing_labs_row and existing_labs_row['count'] == 0:
        print("INFO: Nenhum laboratório encontrado. Inserindo laboratórios iniciais.")
        recursos_labcc = json.dumps(["30 Computadores", "Datashow", "Ar Condicionado", "Quadro Digital"])
        recursos_labcan = json.dumps(["25 Computadores", "Datashow", "Ar Condicionado"])
        laboratorios_iniciais = [
            ('LabCC', 'Bloco A - Sala 101', 30, recursos_labcc),
            ('LabCan', 'Campus Natal - Sala 201', 25, recursos_labcan)
        ]
        for lab_data in laboratorios_iniciais:
            conn.execute('''
                INSERT OR IGNORE INTO laboratorios 
                (nome, localizacao, capacidade, recursos, status) 
                VALUES (?, ?, ?, ?, 'disponivel')
            ''', lab_data)
        conn.commit()
    else:
        print("INFO: Laboratórios já existem ou não foi possível verificar. Não inserindo laboratórios iniciais.")
    # --- FIM DA LÓGICA AJUSTADA ---
    
    conn.close()

# --- O RESTANTE DO ARQUIVO app.py (decorators, rotas, if __name__ == '__main__':) PERMANECE O MESMO ---
# Copie as suas funções token_required, admin_required e todas as suas rotas (@app.route(...)) aqui.

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token: return jsonify({'error': 'Token de acesso requerido'}), 401
        try:
            if token.startswith('Bearer '): token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = data
        except jwt.ExpiredSignatureError: return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError: return jsonify({'error': 'Token inválido'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.get('tipo') != 'admin':
            return jsonify({'error': 'Acesso negado - privilégios administrativos necessários'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('matricula') or not data.get('senha'):
        return jsonify({'error': 'Matrícula e senha são obrigatórios'}), 400
    conn = get_db_connection()
    user_row = conn.execute(
        'SELECT * FROM professores WHERE matricula = ? AND status = "ativo"', (data['matricula'],)
    ).fetchone()
    conn.close()
    if not user_row:
        return jsonify({'error': 'Credenciais inválidas ou usuário inativo'}), 401
    user = dict(user_row) # Convertido para dict
    user_type = user.get('tipo', 'professor')
    if bcrypt.checkpw(data['senha'].encode('utf-8'), user['senha_hash']):
        token = jwt.encode({
            'id': user['id'], 'matricula': user['matricula'], 'nome': user['nome_completo'],
            'email': user.get('email'), 'departamento': user.get('departamento', ''), 'tipo': user_type,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({
            'token': token, 'user': { 'id': user['id'], 'nome': user['nome_completo'],
                'matricula': user['matricula'], 'email': user.get('email'),
                'departamento': user.get('departamento', ''), 'telefone': user.get('telefone', ''),
                'tipo': user_type }})
    else:
        return jsonify({'error': 'Credenciais inválidas'}), 401

@app.route('/api/laboratorios', methods=['GET'])
@token_required
def get_laboratorios(current_user):
    conn = get_db_connection()
    laboratorios = conn.execute(
        'SELECT * FROM laboratorios WHERE status = "disponivel" ORDER BY nome'
    ).fetchall()
    conn.close()
    result = []
    for lab_row in laboratorios:
        lab_dict = dict(lab_row)
        try:
            lab_dict['recursos'] = json.loads(lab_dict['recursos'] or '[]')
        except json.JSONDecodeError:
            lab_dict['recursos'] = [] # Trata caso o JSON seja inválido
        result.append(lab_dict)
    return jsonify(result)

@app.route('/api/verificar-disponibilidade', methods=['POST'])
@token_required
def verificar_disponibilidade(current_user):
    data = request.get_json()
    required_fields = ['laboratorio_id', 'data', 'horario_inicio', 'horario_fim']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Dados incompletos'}), 400
    
    # NOVO: Pega o ID da reserva a ser excluída da verificação, se fornecido (para edição)
    reserva_id_excluir = data.get('reserva_id_excluir', 0) # 0 não deve colidir com IDs reais

    conn = get_db_connection()
    # ALTERADO: Adiciona `AND id != ?` à query de conflitos
    query = '''
        SELECT * FROM reservas 
        WHERE laboratorio_id = ? AND data = ? AND status != 'cancelada' AND id != ?
        AND (
            (horario_inicio < ? AND horario_fim > ?) OR
            (horario_inicio < ? AND horario_fim > ?) OR
            (horario_inicio >= ? AND horario_fim <= ?)
        )
    '''
    params = (
        data['laboratorio_id'], data['data'], reserva_id_excluir,
        data['horario_fim'], data['horario_inicio'],
        data['horario_inicio'], data['horario_fim'],
        data['horario_inicio'], data['horario_fim']
    )
    conflitos = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify({'disponivel': len(conflitos) == 0, 'conflitos': len(conflitos)})


@app.route('/api/reservas', methods=['POST'])
@token_required
def criar_reserva(current_user):
    data = request.get_json()
    required_fields = ['laboratorio_id', 'data', 'horario_inicio', 'horario_fim', 'disciplina', 'turma']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Dados incompletos'}), 400
    conn = get_db_connection()
    conflitos = conn.execute('''
        SELECT * FROM reservas 
        WHERE laboratorio_id = ? AND data = ? AND status != 'cancelada'
        AND (
            (horario_inicio < ? AND horario_fim > ?) OR
            (horario_inicio < ? AND horario_fim > ?) OR
            (horario_inicio >= ? AND horario_fim <= ?)
        )
    ''', (
        data['laboratorio_id'], data['data'],
        data['horario_fim'], data['horario_inicio'],
        data['horario_inicio'], data['horario_fim'],
        data['horario_inicio'], data['horario_fim']
    )).fetchall()
    if conflitos:
        conn.close()
        return jsonify({'error': 'Horário não disponível, há conflito com outra reserva.'}), 409 # Usar 409 Conflict
    try:
        cursor = conn.execute('''
            INSERT INTO reservas 
            (professor_id, laboratorio_id, data, horario_inicio, horario_fim, 
             disciplina, turma, descricao_atividade, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'confirmada')
        ''', (
            current_user['id'], data['laboratorio_id'], data['data'],
            data['horario_inicio'], data['horario_fim'], data['disciplina'],
            data['turma'], data.get('descricao_atividade', '')
        ))
        conn.commit()
        reserva_id = cursor.lastrowid
        conn.close()
        return jsonify({'message': 'Reserva criada com sucesso', 'reserva_id': reserva_id}), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': f'Erro ao criar reserva: {str(e)}'}), 500

@app.route('/api/minhas-reservas', methods=['GET'])
@token_required
def get_minhas_reservas(current_user):
    conn = get_db_connection()
    reservas = conn.execute('''
        SELECT r.*, l.nome as laboratorio_nome, l.localizacao
        FROM reservas r JOIN laboratorios l ON r.laboratorio_id = l.id
        WHERE r.professor_id = ? ORDER BY r.data DESC, r.horario_inicio DESC
    ''', (current_user['id'],)).fetchall()
    conn.close()
    return jsonify([dict(reserva) for reserva in reservas])

@app.route('/api/reservas/<int:reserva_id>', methods=['GET']) # ROTA PARA BUSCAR UMA RESERVA (para edição)
@token_required
def get_reserva_by_id(current_user, reserva_id):
    conn = get_db_connection()
    reserva = conn.execute('SELECT * FROM reservas WHERE id = ?', (reserva_id,)).fetchone()
    conn.close()
    if not reserva: return jsonify({'error': 'Reserva não encontrada'}), 404
    if reserva['professor_id'] != current_user['id'] and current_user.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso não autorizado'}), 403
    return jsonify(dict(reserva))

@app.route('/api/reservas/<int:reserva_id>', methods=['PUT']) # ROTA PARA ATUALIZAR RESERVA
@token_required
def update_reserva(current_user, reserva_id):
    data = request.get_json()
    required_fields = ['laboratorio_id', 'data', 'horario_inicio', 'horario_fim', 'disciplina', 'turma']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Dados incompletos para atualização'}), 400
    conn = get_db_connection()
    reserva_original = conn.execute('SELECT * FROM reservas WHERE id = ?', (reserva_id,)).fetchone()
    if not reserva_original:
        conn.close(); return jsonify({'error': 'Reserva não encontrada para atualizar'}), 404
    if reserva_original['professor_id'] != current_user['id'] and current_user.get('tipo') != 'admin': # Admin também pode editar
        conn.close(); return jsonify({'error': 'Acesso não autorizado para editar esta reserva'}), 403
    
    # Verifica conflitos, ignorando a própria reserva que está sendo editada
    conflitos = conn.execute('''
        SELECT * FROM reservas 
        WHERE laboratorio_id = ? AND data = ? AND status != 'cancelada' AND id != ? 
        AND (
            (horario_inicio < ? AND horario_fim > ?) OR
            (horario_inicio < ? AND horario_fim > ?) OR
            (horario_inicio >= ? AND horario_fim <= ?)
        )
    ''', (
        data['laboratorio_id'], data['data'], reserva_id,
        data['horario_fim'], data['horario_inicio'],
        data['horario_inicio'], data['horario_fim'],
        data['horario_inicio'], data['horario_fim']
    )).fetchall()
    if conflitos:
        conn.close(); return jsonify({'error': 'Horário não disponível, conflito com outra reserva.'}), 409

    try:
        conn.execute('''
            UPDATE reservas SET
                laboratorio_id = ?, data = ?, horario_inicio = ?, horario_fim = ?,
                disciplina = ?, turma = ?, descricao_atividade = ?, status = ?
            WHERE id = ?
        ''', (
            data['laboratorio_id'], data['data'], data['horario_inicio'], data['horario_fim'],
            data['disciplina'], data['turma'], data.get('descricao_atividade', ''),
            data.get('status', reserva_original['status']), # Permite atualizar status se enviado, senão mantém o original
            reserva_id
        ))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Reserva atualizada com sucesso'}), 200
    except Exception as e:
        conn.close(); return jsonify({'error': f'Erro ao atualizar reserva: {str(e)}'}), 500

@app.route('/api/reservas/<int:reserva_id>/cancelar', methods=['PUT'])
@token_required
def cancelar_reserva(current_user, reserva_id):
    conn = get_db_connection()
    # Verifica se o usuário é o dono ou admin
    reserva = conn.execute('SELECT professor_id FROM reservas WHERE id = ?', (reserva_id,)).fetchone()
    if not reserva:
        conn.close(); return jsonify({'error': 'Reserva não encontrada'}), 404
    
    can_cancel = False
    if current_user.get('tipo') == 'admin':
        can_cancel = True
    elif reserva['professor_id'] == current_user['id']:
        can_cancel = True
        
    if not can_cancel:
        conn.close(); return jsonify({'error': 'Você não tem permissão para cancelar esta reserva'}), 403

    cursor = conn.execute("UPDATE reservas SET status = 'cancelada' WHERE id = ?", (reserva_id,))
    conn.commit()
    if cursor.rowcount == 0: # Já verificado acima, mas uma dupla checagem
        conn.close(); return jsonify({'error': 'Reserva não encontrada ou já estava no estado desejado'}), 404
    conn.close()
    return jsonify({'message': 'Reserva cancelada com sucesso'})

@app.route('/api/dashboard', methods=['GET'])
@token_required
def get_dashboard(current_user):
    conn = get_db_connection()
    total_reservas = conn.execute(
        'SELECT COUNT(*) as total FROM reservas WHERE professor_id = ?', (current_user['id'],)
    ).fetchone()['total']
    reservas_confirmadas = conn.execute(
        'SELECT COUNT(*) as total FROM reservas WHERE professor_id = ? AND status = "confirmada"', (current_user['id'],)
    ).fetchone()['total']
    proximas_reservas = conn.execute('''
        SELECT r.*, l.nome as laboratorio_nome, l.localizacao
        FROM reservas r JOIN laboratorios l ON r.laboratorio_id = l.id
        WHERE r.professor_id = ? AND r.data >= date('now') AND r.status = 'confirmada'
        ORDER BY r.data ASC, r.horario_inicio ASC LIMIT 5
    ''', (current_user['id'],)).fetchall()
    conn.close()
    return jsonify({
        'totalReservas': total_reservas, 'reservasConfirmadas': reservas_confirmadas,
        'proximasReservas': [dict(reserva) for reserva in proximas_reservas]
    })

@app.route('/api/reservas-calendario', methods=['GET'])
@token_required
def get_reservas_for_calendar(current_user):
    conn = get_db_connection()
    reservas = conn.execute('''
        SELECT r.id, r.data, r.horario_inicio, r.horario_fim, r.status, r.disciplina, r.turma,
               l.nome as laboratorio_nome, p.nome_completo as professor_nome
        FROM reservas r
        JOIN laboratorios l ON r.laboratorio_id = l.id
        JOIN professores p ON r.professor_id = p.id
        WHERE r.status != 'cancelada' ORDER BY r.data, r.horario_inicio
    ''').fetchall()
    conn.close()
    # Não há necessidade de mapear para `events` aqui; o frontend pode fazer isso.
    # Apenas retorna a lista de reservas como dicionários.
    return jsonify([dict(res) for res in reservas])


# --- ROTAS ADMINISTRATIVAS ---
@app.route('/api/professores', methods=['GET'])
@token_required
@admin_required
def listar_todos_professores(current_user):
    conn = get_db_connection()
    professores = conn.execute(
        'SELECT id, nome_completo, matricula, email, telefone, departamento, status, tipo, created_at FROM professores ORDER BY nome_completo'
    ).fetchall()
    conn.close()
    return jsonify([dict(prof) for prof in professores])

@app.route('/api/professores', methods=['POST'])
@token_required
@admin_required
def criar_professor(current_user):
    data = request.get_json()
    required_fields = ['nome_completo', 'matricula', 'senha'] # Email é opcional no DB schema
    if not all(data.get(field) for field in required_fields):
        return jsonify({'error': 'Nome, matrícula e senha são obrigatórios.'}), 400
    senha_hash = bcrypt.hashpw(data['senha'].encode('utf-8'), bcrypt.gensalt())
    conn = get_db_connection()
    try:
        cursor = conn.execute('''
            INSERT INTO professores (nome_completo, matricula, email, telefone, departamento, senha_hash, status, tipo)
            VALUES (?, ?, ?, ?, ?, ?, 'ativo', 'professor') 
        ''', (
            data['nome_completo'], data['matricula'], data.get('email'), 
            data.get('telefone', ''), data.get('departamento', ''), senha_hash
        ))
        conn.commit()
        professor_id = cursor.lastrowid
        conn.close()
        return jsonify({'message': 'Professor criado com sucesso', 'professor_id': professor_id}), 201
    except sqlite3.IntegrityError as e:
        conn.close()
        if 'matricula' in str(e).lower(): return jsonify({'error': 'Matrícula já existe'}), 409
        if 'email' in str(e).lower() and data.get('email'): return jsonify({'error': 'Email já existe'}), 409
        return jsonify({'error': f'Erro de integridade: {e}'}), 409
    except Exception as e:
        conn.close(); return jsonify({'error': f'Erro interno: {e}'}), 500

@app.route('/api/professores/<int:professor_id>', methods=['DELETE'])
@token_required
@admin_required
def deletar_professor(current_user, professor_id):
    conn = get_db_connection()
    # ON DELETE CASCADE cuidará das reservas
    cursor = conn.execute('DELETE FROM professores WHERE id = ?', (professor_id,))
    conn.commit()
    conn.close()
    if cursor.rowcount == 0: return jsonify({'error': 'Professor não encontrado'}), 404
    return jsonify({'message': 'Professor deletado com sucesso'})

@app.route('/api/laboratorios', methods=['POST'])
@token_required
@admin_required
def criar_laboratorio(current_user):
    data = request.get_json()
    required_fields = ['nome', 'localizacao', 'capacidade']
    if not all(data.get(field) for field in required_fields):
        return jsonify({'error': 'Nome, localização e capacidade são obrigatórios.'}), 400
    try:
        capacidade = int(data['capacidade'])
        if capacidade <= 0: raise ValueError("Capacidade deve ser positiva.")
    except (ValueError, TypeError):
        return jsonify({'error': 'Capacidade deve ser um número inteiro positivo.'}), 400
    conn = get_db_connection()
    try:
        cursor = conn.execute('''
            INSERT INTO laboratorios (nome, localizacao, capacidade, recursos, status)
            VALUES (?, ?, ?, ?, 'disponivel')
        ''', (
            data['nome'], data['localizacao'], capacidade, 
            json.dumps(data.get('recursos', []) or [])
        ))
        conn.commit()
        lab_id = cursor.lastrowid
        conn.close()
        return jsonify({'message': 'Laboratório criado com sucesso', 'laboratorio_id': lab_id}), 201
    except sqlite3.IntegrityError as e: # Ex. nome do lab único, se definido no DB
        conn.close(); return jsonify({'error': f'Erro de integridade: {e}'}), 409
    except Exception as e:
        conn.close(); return jsonify({'error': f'Erro interno: {e}'}), 500

@app.route('/api/laboratorios/<int:laboratorio_id>', methods=['DELETE'])
@token_required
@admin_required
def deletar_laboratorio(current_user, laboratorio_id):
    conn = get_db_connection()
    # ON DELETE CASCADE cuidará das reservas
    cursor = conn.execute('DELETE FROM laboratorios WHERE id = ?', (laboratorio_id,))
    conn.commit()
    conn.close()
    if cursor.rowcount == 0: return jsonify({'error': 'Laboratório não encontrado'}), 404
    return jsonify({'message': 'Laboratório deletado com sucesso'})

@app.route('/api/reservas-admin', methods=['GET'])
@token_required
@admin_required
def get_all_reservas_admin(current_user):
    conn = get_db_connection()
    reservas = conn.execute('''
        SELECT r.*, l.nome as laboratorio_nome, l.localizacao, p.nome_completo as professor_nome
        FROM reservas r 
        JOIN laboratorios l ON r.laboratorio_id = l.id
        JOIN professores p ON r.professor_id = p.id
        ORDER BY r.data DESC, r.horario_inicio DESC
    ''').fetchall()
    conn.close()
    return jsonify([dict(reserva) for reserva in reservas])

@app.route('/api/reservas/<int:reserva_id>/status', methods=['PUT'])
@token_required
@admin_required
def update_reserva_status(current_user, reserva_id):
    data = request.get_json()
    new_status = data.get('status')
    if new_status not in ['confirmada', 'pendente', 'cancelada']:
        return jsonify({'error': 'Status inválido'}), 400
    conn = get_db_connection()
    cursor = conn.execute('UPDATE reservas SET status = ? WHERE id = ?', (new_status, reserva_id))
    conn.commit()
    conn.close()
    if cursor.rowcount == 0: return jsonify({'error': 'Reserva não encontrada'}), 404
    return jsonify({'message': f'Status da reserva atualizado para {new_status}'})

if __name__ == '__main__':
    print("🚀 Inicializando Sistema de Agendamento - UERN")
    print("="*50)
    print("📊 Inicializando banco de dados...")
    init_database() # Chama a função ajustada
    print("✅ Banco de dados inicializado!")
    print("\n🔐 Credenciais de teste:")
    print("👤 Professor: Matrícula: 123456, Senha: 123456")
    print("👑 Admin: Matrícula: 999999, Senha: admin123")
    print(f"\n🌐 Servidor rodando em http://localhost:5000")
    print("="*50)
    app.run(debug=True, host='0.0.0.0', port=5000)