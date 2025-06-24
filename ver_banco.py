# ver_banco.py
# Execute: python ver_banco.py

import sqlite3
import json

def main():
    try:
        # Conectar ao banco
        conn = sqlite3.connect('agendamento.db')
        conn.row_factory = sqlite3.Row
        
        print("🎯 VISUALIZADOR DO BANCO - AGENDAMENTO UERN")
        print("="*50)
        
        # Listar tabelas
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tabelas = [row[0] for row in cursor.fetchall()]
        print(f"📋 Tabelas encontradas: {', '.join(tabelas)}")
        
        # Mostrar professores
        print("\n👥 PROFESSORES:")
        cursor = conn.execute("SELECT * FROM professores ORDER BY nome_completo")
        professores = cursor.fetchall()
        
        for prof in professores:
            tipo_icon = "👑" if prof['tipo'] == 'admin' else "👤"
            status_icon = "✅" if prof['status'] == 'ativo' else "❌"
            print(f"  {tipo_icon} {status_icon} {prof['nome_completo']}")
            print(f"      ID: {prof['id']} | Matrícula: {prof['matricula']}")
            print(f"      Email: {prof['email'] or 'N/A'}")
            print(f"      Departamento: {prof['departamento'] or 'N/A'}")
            print()
        
        # Mostrar laboratórios
        print("🔬 LABORATÓRIOS:")
        cursor = conn.execute("SELECT * FROM laboratorios ORDER BY nome")
        laboratorios = cursor.fetchall()
        
        for lab in laboratorios:
            status_icon = "✅" if lab['status'] == 'disponivel' else "❌"
            print(f"  {status_icon} {lab['nome']} - {lab['localizacao']}")
            print(f"      ID: {lab['id']} | Capacidade: {lab['capacidade']} pessoas")
            
            # Decodificar recursos
            try:
                recursos = json.loads(lab['recursos'] or '[]')
                if recursos:
                    print(f"      Recursos: {', '.join(recursos)}")
            except:
                print(f"      Recursos: {lab['recursos'] or 'N/A'}")
            print()
        
        # Mostrar reservas
        print("📅 RESERVAS:")
        cursor = conn.execute("""
            SELECT 
                r.id, r.data, r.horario_inicio, r.horario_fim,
                r.disciplina, r.turma, r.status,
                p.nome_completo as professor,
                l.nome as laboratorio
            FROM reservas r
            JOIN professores p ON r.professor_id = p.id
            JOIN laboratorios l ON r.laboratorio_id = l.id
            ORDER BY r.data DESC, r.horario_inicio DESC
            LIMIT 10
        """)
        reservas = cursor.fetchall()
        
        if reservas:
            for res in reservas:
                status_icon = {"confirmada": "✅", "cancelada": "❌", "pendente": "⏳"}.get(res['status'], "❓")
                print(f"  {status_icon} Reserva #{res['id']} - {res['data']} ({res['horario_inicio']}-{res['horario_fim']})")
                print(f"      Professor: {res['professor']}")
                print(f"      Lab: {res['laboratorio']} | {res['disciplina']} - {res['turma']}")
                print()
        else:
            print("  ❌ Nenhuma reserva encontrada")
        
        # Estatísticas
        print("📊 ESTATÍSTICAS:")
        for tabela in ['professores', 'laboratorios', 'reservas']:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {tabela}")
            total = cursor.fetchone()[0]
            print(f"  • {tabela.title()}: {total}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Erro no banco: {e}")
    except FileNotFoundError:
        print("❌ Arquivo 'agendamento.db' não encontrado!")
        print("Execute sua aplicação Flask primeiro para criar o banco.")

if __name__ == "__main__":
    main()