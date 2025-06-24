# 📅 Sistema de Agendamento - LabCC e LabCan (UERN)

Sistema web moderno para agendamento e reserva dos laboratórios de informática da UERN, desenvolvido com Python Flask e interface moderna.

## 👥 Equipe de Desenvolvimento

- **Diogo Gonçalves** - Backend, API e Banco de Dados
- **Luziane Paulino dos Santos** - Frontend, Interface e UX/UI

**Disciplina:** Prática de Programação II  
**Professor:** André Gustavo  
**Instituição:** UERN - Campus Avançado de Natal  
**Período:** 2025.1

## 🎯 Sobre o Projeto

Sistema completo de agendamento para os laboratórios LabCC (Laboratório de Ciência da Computação) e LabCan (Laboratório do Campus Avançado de Natal), permitindo que professores façam reservas de forma eficiente, evitando conflitos de horários e otimizando o uso dos espaços.

## 🛠️ Stack Tecnológica

### **Backend:**
- **Python 3.7+** - Linguagem principal
- **Flask 2.3.3** - Framework web
- **SQLite** - Banco de dados
- **JWT** - Autenticação
- **bcrypt** - Criptografia de senhas

### **Frontend:**
- **HTML5** - Estrutura
- **CSS3 + Tailwind** - Estilização
- **JavaScript (Vanilla)** - Interatividade
- **Lucide Icons** - Iconografia
- **Glassmorphism** - Design moderno

## 📋 Pré-requisitos

- **Python 3.7 ou superior**
- **pip** (gerenciador de pacotes Python)
- **Navegador moderno** (Chrome, Firefox, Safari, Edge)

## ⚡ Instalação e Execução

### **1. 📁 Preparar o ambiente:**
```bash
# Clone ou baixe o projeto
git clone https://github.com/luizianesp/Projeto-labcc-e-labcan.git
cd Projeto-labcc-e-labcan

# Ou extraia o arquivo ZIP baixado
```

### **2. 📦 Instalar dependências:**
```bash
pip install -r requirements.txt
```

### **3. 🚀 Executar o sistema:**
```bash
python app.py
```

### **4. 🌐 Acessar o sistema:**
Abra seu navegador em: **http://localhost:5000**

## 🔐 Credenciais de Teste

O sistema vem com professores pré-cadastrados:

| Professor | Matrícula | Senha | Departamento |
|-----------|-----------|-------|--------------|
| **Prof. André Gustavo** | `123456` | `123456` | Ciência da Computação |
| **Prof. Maria Silva** | `123457` | `123456` | Ciência da Computação |


## 🔄 Em Desenvolvimento (3ª Unidade)

### **🎯 PRIORIDADE ALTA:**
- [ ] **📅 Calendário Visual** - Vista mensal/semanal dos laboratórios
- [ ] **📊 Sistema de Relatórios** - Ocupação, períodos, exportação
- [ ] **👤 Perfil do Usuário** - Edição de dados pessoais

### **🎯 PRIORIDADE MÉDIA:**
- [ ] **🔧 Painel Administrativo** - CRUD de professores e laboratórios
- [ ] **🔔 Sistema de Notificações** - Lembretes e confirmações
- [ ] **🔍 Busca Avançada** - Filtros e paginação

## 📊 Estrutura do Banco de Dados

### **👨‍🏫 Tabela `professores`**
```sql
id, nome_completo, matricula, email, telefone, 
departamento, senha_hash, created_at
```

### **🏢 Tabela `laboratorios`**
```sql
id, nome, localizacao, capacidade, recursos (JSON), 
status, created_at
```

### **📅 Tabela `reservas`**
```sql
id, professor_id, laboratorio_id, data, horario_inicio, 
horario_fim, disciplina, turma, descricao_atividade, 
status, created_at
```

## 🛣️ API Endpoints

| Método | Endpoint | Autenticação | Descrição |
|--------|----------|--------------|-----------|
| `GET` | `/` | ❌ | Página principal (frontend) |
| `POST` | `/api/login` | ❌ | Autenticação do professor |
| `GET` | `/api/laboratorios` | 🔒 | Lista laboratórios disponíveis |
| `POST` | `/api/verificar-disponibilidade` | 🔒 | Verifica conflitos de horário |
| `POST` | `/api/reservas` | 🔒 | Criar nova reserva |
| `GET` | `/api/minhas-reservas` | 🔒 | Lista reservas do professor |
| `PUT` | `/api/reservas/<id>/cancelar` | 🔒 | Cancelar reserva específica |
| `GET` | `/api/dashboard` | 🔒 | Dados estatísticos |

**🔒 = Requer token JWT no header Authorization**

## 📁 Estrutura do Projeto

```
sistema-agendamento-labs/
│
├── 🐍 app.py                    # Backend Flask (400+ linhas)
├── 📦 requirements.txt          # Dependências Python
├── 📄 README.md                 # Este arquivo
│
├── 📁 templates/
│   └── 🎨 index.html           # Frontend completo (1200+ linhas)
│
└── 🗄️ agendamento.db            # Banco SQLite (auto-gerado)
    ├── Tabela professores
    ├── Tabela laboratorios
    └── Tabela reservas
```

## 🔧 Resolução de Problemas

### **❗ Erro: "Erro de conexão com o servidor"**
```bash
# 1. Verificar se o servidor está rodando
python app.py

# 2. Acessar exatamente: http://localhost:5000
# 3. Verificar firewall/antivírus
```

### **❗ Erro de dependências**
```bash
# Atualizar pip e reinstalar
pip install --upgrade pip
pip install -r requirements.txt
```

🎉 Status do Projeto
🎯 PROJETO 75% CONCLUÍDO
O sistema está funcionalmente completo para uso básico, com interface moderna e backend robusto. Todas as funcionalidades core estão implementadas e testadas.
⭐ Destaque: Interface visual de alta qualidade com glassmorphism, animações e UX profissional.

Desenvolvido com ❤️ para UERN - 2025
Diogo Gonçalves & Luziane Paulino dos Santos
