from flask import Flask, redirect, url_for, flash, g, jsonify, render_template, request, session
import sqlite3, pytz
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'  # Substitua 'sua_chave_secreta' por uma chave segura

fuso_horario_brasil = pytz.timezone('America/Sao_Paulo')

data_e_hora_brasil = datetime.now(fuso_horario_brasil)

# Função para conectar ao banco de dados
def connect_db():
    return sqlite3.connect('app.db')


# Rota para criar o banco de dados (somente uma vez)
@app.route('/create_db')
def create_db():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL,
            telefone TEXT NOT NULL,
            senha TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS burguers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            preco DECIMAL(10, 2) NOT NULL,
            disponivel BOOLEAN DEFAULT 1,
            imagem_url TEXT,
            data_adicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            burguer_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos (id),
            FOREIGN KEY (burguer_id) REFERENCES burguers (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS avaliacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            burguer_id INTEGER NOT NULL,
            pedido_id INTEGER NOT NULL,
            classificacao INTEGER NOT NULL,
            comentario TEXT,
            FOREIGN KEY (burguer_id) REFERENCES burguers (id),
            FOREIGN KEY (pedido_id) REFERENCES pedidos (id)
        )
    ''')

    conn.commit()
    conn.close()

    flash('Banco de dados criado com sucesso', 'success')
    return redirect(url_for('login'))


DATABASE = 'app.db'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def get_burguers_from_database():
    burguers = []

    try:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM burguers')
        burguers_data = cursor.fetchall()

        for burguer_data in burguers_data:
            burguer = {
                'id': burguer_data[0],
                'nome': burguer_data[1],
                'descricao': burguer_data[2],
                'preco': burguer_data[3],
                'disponivel': burguer_data[4],
                'imagem_url': burguer_data[5],
                'data_adicao': burguer_data[6]
            }
            burguers.append(burguer)

        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print('Erro ao buscar hambúrguer do banco de dados:', str(e))

    return burguers


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM usuarios WHERE email = ? AND senha = ?', (email, senha))
        usuario = cursor.fetchone()

        conn.commit()
        conn.close()

        if usuario:
            session['usuario_id'] = usuario[0]

            if usuario[5] == 1:
                return redirect(url_for('adm_Dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Falha ao tentar logar.', 'error')

    return render_template('login.html')

@app.route('/atualizar_burguer/<int:burguer_id>', methods=['POST'])
def atualizar_burguer(burguer_id):
    try:
        # Recuperar os dados enviados pelo formulário
        novo_nome = request.form['nome']
        nova_descricao = request.form['descricao']
        novo_preco = request.form['preco']
        disponivel = 'disponivel' in request.form

        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE burguers
            SET nome = ?, descricao = ?, preco = ?, disponivel = ?
            WHERE id = ?
        ''', (novo_nome, nova_descricao, novo_preco, disponivel, burguer_id))

        conn.commit()
        conn.close()

        # Redirecionar de volta para a página de listagem de hambugueres após a atualização
        session['mensagem'] = 'Hambúrguer atualizado com sucesso!'
        return redirect('/adm_Dashboard')

    except Exception as e:
        session['mensagem'] = f'Erro ao atualizar o burguer: {str(e)}'
        return redirect('/adm_Dashboard')


@app.route('/adm_EditBurguer/<int:burguer_id>', methods=['GET'])
def adm_EditBurguer(burguer_id):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    # Execute uma consulta SQL para recuperar os detalhes do burguer com o burguer_id fornecido
    cursor.execute('SELECT * FROM burguers WHERE id = ?', (burguer_id,))
    burguer = cursor.fetchone()

    # Feche a conexão com o banco de dados
    conn.close()

    # Verifique se o burguer foi encontrado com o ID fornecido
    if burguer:
        # Renderize a página de edição adm_EditBurguer.html, passando os detalhes do burguer
        return render_template('adm_EditBurguer.html', burguer=burguer)
    else:
        # Se o burguer com o ID fornecido não for encontrado, redirecione para outra página ou manipule conforme necessário
        return "Hambúrguer não encontrado"

def get_pedidos():
    # Conexão com o banco de dados (SQLite como exemplo)
    conn = sqlite3.connect('app.db')  # Substitua 'banco.db' pelo seu banco de dados
    cursor = conn.cursor()
    
    # Consulta SQL para buscar dados
    cursor.execute("SELECT id, usuario_id, data_pedido, status FROM pedidos")  # Ajuste conforme sua tabela
    pedidos = cursor.fetchall()
    
    conn.close()
    return pedidos

@app.route('/adm_Customer')
def adm_Customer():
    # Obtenha os pedidos
    usuarios = get_usuarios()
    
    # Renderize o template com os dados
    return render_template('adm_Customer.html', usuarios=usuarios)

def get_usuarios():
    # Conexão com o banco de dados (SQLite como exemplo)
    conn = sqlite3.connect('app.db')  # Substitua 'banco.db' pelo seu banco de dados
    cursor = conn.cursor()
    
    # Consulta SQL para buscar dados
    cursor.execute("SELECT id, nome, email, telefone, is_admin, endereco FROM usuarios")  # Ajuste conforme sua tabela
    usuarios = cursor.fetchall()
    
    conn.close()
    return usuarios

@app.route('/adm_Orders')
def adm_Orders():
    # Obtenha os pedidos
    relatorios = get_relatorioPedidos()
    
    # Renderize o template com os dados
    return render_template('adm_Orders.html', relatorios=relatorios)

def get_relatorioPedidos():
    # Conexão com o banco de dados (SQLite como exemplo)
    conn = sqlite3.connect('app.db')  # Substitua 'banco.db' pelo seu banco de dados
    cursor = conn.cursor()
    
    # Consulta SQL para buscar dados
    cursor.execute("""SELECT 
    u.nome AS Cliente,
    u.telefone,
    u.endereco,
    b.nome AS Hamburguer,
    ip.quantidade,
    p.data_pedido AS DataPedido,
    p.status AS StatusPedido,
    p.id AS PedidoID
FROM 
    itens_pedido ip
INNER JOIN 
    pedidos p ON ip.pedido_id = p.id
INNER JOIN 
    burguers b ON ip.burguer_id = b.id
INNER JOIN 
    usuarios u ON p.usuario_id = u.id;""")
    relatorios = cursor.fetchall()
    
    conn.close()
    return relatorios

# Rota para o dashboard (requer login)
@app.route('/dashboard')
def dashboard():
    if 'usuario_id' in session:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM usuarios WHERE id = ?', (session['usuario_id'],))
        usuario = cursor.fetchone()

        # Buscar os hambugueres do banco de dados (ou de outra fonte)
        burguers = get_burguers_from_database()

        conn.commit()
        conn.close()

        if usuario:
            return render_template('dashboard.html', usuario=usuario, burguers=burguers)

    flash('Faça o login para acessar o dashboard', 'error')
    return redirect(url_for('login'))


@app.route('/adm_Dashboard')
def adm_Dashboard():
    if 'usuario_id' in session:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE id = ?', (session['usuario_id'],))
        usuario = cursor.fetchone()

        #fazer um drop table de cupcakes
        #cursor.execute('''DROP table cupcakes;''')
        
        conn.commit()
        conn.close()
        if usuario:
            # Verificar se o usuário é um administrador
            if usuario[5] == 1:
                return render_template('adm_Dashboard.html')
            else:
                flash('Você não tem permissão para acessar a página de administração', 'error')
                return redirect(
                    url_for('dashboard'))  # Redireciona para o painel normal se o usuário não for administrador
        else:
            flash('Faça o login para acessar a página de administração', 'error')
            return redirect(url_for('login'))

    flash('Faça o login para acessar a página de administração', 'error')
    return redirect(url_for('login'))


# Rota para logout
@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    return redirect(url_for('login'))


# Rota para o formulário de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        endereco = request.form['endereco']
        senha = request.form['senha']
        confirmar_senha = request.form['confirmar_senha']  # Adicione a confirmação de senha
        telefone = request.form['telefone']

        # Verifique se a senha e a confirmação de senha correspondem
        if senha != confirmar_senha:
            flash('A senha e a confirmação de senha não correspondem. Por favor, tente novamente.', 'error')
        else:
            conn = connect_db()
            cursor = conn.cursor()

            # Verifique se o email já está em uso
            cursor.execute('SELECT * FROM usuarios WHERE email = ?', (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash('Este email já está associado a uma conta existente. Por favor, faça login ou use outro email.',
                      'error')
            else:
                cursor.execute('INSERT INTO usuarios (nome, endereco, email, senha) VALUES (?, ?, ?, ?)', (nome, endereco, email, senha))
                conn.commit()
                conn.close()
                flash('Usuário registrado com sucesso', 'success')
                return redirect(url_for('login'))

    return render_template('register.html')


def is_admin():
    # Verifique se a variável de sessão "admin" está definida como True
    return session.get('admin', False)


@app.route('/adm_ListaBurguer', methods=['GET'])
def list_burguers():
    # Estabeleça uma conexão com o banco de dados
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    # Execute uma consulta SQL para listar todos os burguers
    cursor.execute('SELECT * FROM burguers')

    # Recupere todos os hambugueres do banco de dados
    burguers = cursor.fetchall()

    # Feche a conexão com o banco de dados
    conn.close()

    return render_template('adm_ListaBurguer.html', burguers=burguers)


# Função para obter informações do burguer com base no ID no banco de dados
def obter_burguer(burguer_id):
    try:
        # Conectar ao banco de dados SQLite
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()

        # Executar uma consulta SQL para buscar o burguer com base no ID
        cursor.execute('SELECT * FROM burguers WHERE id = ?', (burguer_id,))
        burguer_data = cursor.fetchone()

        if burguer_data:
            burguer_info = {
                'id': burguer_data[0],
                'nome': burguer_data[1],
                'descricao': burguer_data[2],
                'preco': float(burguer_data[3].replace(',', '.')),
                'disponivel': bool(burguer_data[4]),
                'imagem_url': burguer_data[5]
            }

            return burguer_info

    except sqlite3.Error as e:
        # Tratar exceções de banco de dados, se necessário
        print("Erro ao buscar o Hambúrguer:", e)
    finally:
        # Fechar a conexão com o banco de dados
        conn.commit()
        conn.close()

    return None  # Retornar None se o burguer não for encontrado


@app.route('/limpar-carrinho', methods=['POST'])
def limpar_carrinho():
    if 'carrinho' in session and session['carrinho']:
        session.pop('carrinho', None)  # Remove a variável de sessão 'carrinho'
        flash('Carrinho esvaziado.', 'success')
    else:
        flash('O carrinho já está vazio.', 'info')

    return redirect('/carrinho')  # Redireciona de volta para a página do carrinho


@app.route('/adicionar_ao_carrinho', methods=['POST'])
def adicionar_ao_carrinho():
    try:
        # Verifica se 'carrinho' já está na sessão, senão, cria uma lista vazia.
        if 'carrinho' not in session:
            session['carrinho'] = []

        # Obtém os dados do formulário.
        burguer_id = request.form.get('burguer_id')
        quantidade = request.form.get('quantidade', type=int)

        burguer_info = obter_burguer(burguer_id)

        if burguer_info:
            # Verifique se já existe um item com o mesmo burguer_id no carrinho
            for item in session['carrinho']:
                if item['burguer']['id'] == burguer_info['id']:
                    # Se já existe, atualize apenas a quantidade
                    item['quantidade'] += quantidade
                    flash('Quantidade atualizada no carrinho', 'success')
                    break
            else:
                # Se não existe, adicione um novo item ao carrinho
                item = {
                    'burguer': {
                        'id': burguer_info['id'],
                        'nome': burguer_info['nome'],
                        'descricao': burguer_info['descricao'],
                        'preco': burguer_info['preco'],
                        'imagem_url': burguer_info['imagem_url']
                    },
                    'quantidade': quantidade
                }
                session['carrinho'].append(item)
                if quantidade > 1:
                    flash('Hambúrgueres adicionados ao carrinho', 'success')
                else:
                    flash('Hambúrgueres adicionado ao carrinho', 'success')
        else:
            flash('Hambúrguer não encontrado.', 'error')

        return redirect(url_for('carrinho'))
    except Exception as e:
        # Lidar com exceções aqui, se necessário
        return str(e), 500  # Retorna uma resposta de erro 500 com a descrição do erro como texto


@app.route('/remover-do-carrinho/<burguer_id>', methods=['POST'])
def remover_do_carrinho(burguer_id):
    burguer_int = int(burguer_id)
    try:
        if 'carrinho' in session:
            carrinho = session['carrinho']
            # Verifique se já existe um item com o mesmo burguer_id no carrinho
            for item in carrinho:
                print("item:")
                print(type(item['burguer']['id']))
                print(type(burguer_id))
                if item['burguer']['id'] == burguer_int:
                    print(item)
                    # Verifique a quantidade
                    if item['quantidade'] > 1:
                        item['quantidade'] -= 1
                    else:
                        # Se a quantidade for 1, remova o item do carrinho
                        carrinho.remove(item)
                    flash('Hambúrguer removido do carrinho', 'success')
                    break

            # Atualize a sessão com o novo carrinho
            session['carrinho'] = carrinho
        else:
            flash('Carrinho não encontrado na sessão', 'error')

        return redirect(url_for('carrinho'))
    except Exception as e:
        # Lidar com exceções aqui, se necessário
        return str(e), 500  # Retorna uma resposta de erro 500 com a descrição do erro como texto


@app.route('/carrinho', methods=['GET'])
def carrinho():
    if 'carrinho' not in session:
        session['carrinho'] = []

    # Atualize o preço total para cada item no carrinho
    for item in session['carrinho']:
        item['total'] = item['quantidade'] * item['burguer']['preco']

    return render_template('carrinho.html')


# Rota para a página inicial
@app.route('/')
def home():
    return render_template('login.html')


@app.route('/edit_Perfil', methods=['GET', 'POST'])
def edit_Perfil():
    if 'usuario_id' in session:
        if request.method == 'POST':
            nome = request.form['nome']
            endereco = request.form['endereco']
            telefone = request.form['telefone']
            senha = request.form['senha']
            conn = connect_db()
            cursor = conn.cursor()

            # Atualizar as informações do perfil no banco de dados
            cursor.execute('UPDATE usuarios SET nome=?, email=?, endereco=?, telefone=?, senha=? WHERE id=?',
                           (nome, endereco, telefone, senha, session['usuario_id']))
            print(session['usuario_id'])
            conn.commit()
            conn.close()

            flash('Perfil atualizado com sucesso', 'success')
            return redirect(url_for('dashboard'))

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM usuarios WHERE id = ?', (session['usuario_id'],))
        usuario = cursor.fetchone()

        conn.commit()
        conn.close()

        if usuario:
            return render_template('edit_Perfil.html', usuario=usuario)

    flash('Faça o login para acessar o perfil', 'error')
    return redirect(url_for('login'))


@app.route('/adm_AddBurguer', methods=['GET', 'POST'])
def adm_AddBurguer():
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        preco = request.form['preco']
        disponivel = request.form.get('disponivel', False)
        imagem_url = request.form['imagem_url']

        conn = connect_db()
        cursor = conn.cursor()

        # Usar uma transação para garantir atomicidade das operações de banco de dados
        conn.execute('BEGIN')

        cursor.execute('''
        INSERT INTO burguers (nome, descricao, preco, disponivel, imagem_url)
        VALUES (?, ?, ?, ?, ?)
        ''', (nome, descricao, preco, disponivel, imagem_url))

        conn.commit()
        conn.close()

        flash('Produto adicionado com sucesso', 'success')

        return redirect(url_for('adm_Dashboard'))

    return render_template('adm_AddBurguer.html')


@app.route('/finalizar_pedido', methods=['POST'])
def finalizar_pedido():
    if 'carrinho' in session and session['carrinho']:
        carrinho = session['carrinho']
        usuario_id = session.get('usuario_id')
        # Formatando a data e hora para exibir apenas hora e minutos
        data_pedido = data_e_hora_brasil.strftime('%Y-%m-%d %H:%M')

        conn = connect_db()
        cursor = conn.cursor()

        # Crie um registro de pedido no banco de dados
        cursor.execute('INSERT INTO pedidos (usuario_id, data_pedido, status) VALUES (?, ?, ?)', (usuario_id, data_pedido, 'Concluído'))
        pedido_id = cursor.lastrowid

        for item in carrinho:
            burguer_id = item['burguer']['id']
            quantidade = item['quantidade']
            # Crie um registro de item de pedido no banco de dados
            cursor.execute('INSERT INTO itens_pedido (pedido_id, burguer_id, quantidade) VALUES (?, ?, ?)',
                           (pedido_id, burguer_id, quantidade))

        conn.commit()
        conn.close()

        session.pop('carrinho', None)  # Limpe o carrinho após a conclusão do pedido
        flash('Pedido realizado com sucesso', 'success')
    else:
        flash('O carrinho está vazio. Adicione itens ao carrinho antes de finalizar o pedido.', 'danger')

    return redirect(url_for('carrinho'))


@app.route('/avaliar_pedido/<int:pedido_id>', methods=['GET', 'POST'])
def avaliar_pedido(pedido_id):
    # Verifique se o usuário está autenticado
    if 'usuario_id' not in session:
        flash('Faça o login para avaliar o pedido.', 'error')
        return redirect(url_for('login'))



def obter_item_pedido_por_ids(pedido_id):
    item_pedido = None

    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Consulta SQL para buscar o item do pedido com base nos IDs do pedido e do burguer
        cursor.execute('SELECT * FROM itens_pedido WHERE pedido_id = ? AND burguer_id = ?', (pedido_id,))
        item_pedido_data = cursor.fetchone()

        if item_pedido_data:
            item_pedido = {
                'id': item_pedido_data[0],
                'pedido_id': item_pedido_data[1],
                'burguer_id': item_pedido_data[2],
                'quantidade': item_pedido_data[3],
                # Adicione outros campos do item do pedido conforme necessário
            }
            print(item_pedido)

        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print('Erro ao buscar item do pedido do banco de dados:', str(e))

    return item_pedido


def salvar_avaliacao_item_pedido(pedido_id, usuario_id, classificacao, comentario):
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Verifique se já existe uma avaliação para o item do pedido
        cursor.execute('SELECT * FROM avaliacoes WHERE pedido_id = ? AND usuario_id = ?', (pedido_id, usuario_id))
        avaliacao_existente = cursor.fetchone()

        if avaliacao_existente:
            # Se a avaliação já existe, atualize-a
            cursor.execute(
                'UPDATE avaliacoes SET classificacao = ?, comentario = ? WHERE pedido_id = ? AND usuario_id = ?',
                (classificacao, comentario, pedido_id, usuario_id))
        else:
            # Se a avaliação não existe, insira uma nova
            cursor.execute(
                'INSERT INTO avaliacoes (pedido_id, usuario_id, classificacao, comentario) VALUES (?, ?, ?, ?)',
                (pedido_id, usuario_id, classificacao, comentario))

        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print('Erro ao salvar avaliação do item do pedido no banco de dados:', str(e))


def obter_pedidos_realizados():
    try:
        conn = sqlite3.connect('app.db')  # Substitua 'app.db' pelo nome do seu banco de dados
        cursor = conn.cursor()

        # Consulta SQL para obter os pedidos já realizados e os hambugueres relacionados
        cursor.execute('''
            SELECT 
                pedidos.id AS pedido_id, 
                pedidos.usuario_id, 
                pedidos.data_pedido, 
                pedidos.status, 
                itens_pedido.id AS item_pedido_id,
                burguers.id AS burguer_id,
                burguers.nome AS burguer_nome,
                burguers.descricao AS burguer_descricao,
                burguers.preco AS burguer_preco,
                burguers.imagem_url AS burguer_imagem_url,
                itens_pedido.quantidade
            FROM pedidos
            JOIN itens_pedido ON pedidos.id = itens_pedido.pedido_id
            JOIN burguers ON itens_pedido.burguer_id = burguers.id
            WHERE pedidos.status = 'Concluído'
        ''')
        pedidos_data = cursor.fetchall()

        pedidos = []

        for pedido_data in pedidos_data:
            pedido_id = pedido_data[0]

            # Verifique se o pedido já está na lista de pedidos
            pedido_existente = next((pedido for pedido in pedidos if pedido['id'] == pedido_id), None)

            if not pedido_existente:
                # Se o pedido não existe na lista, crie um novo registro
                pedido = {
                    'id': pedido_id,
                    'usuario_id': pedido_data[1],
                    'data_pedido': pedido_data[2],
                    'status': pedido_data[3],
                    'itens': []  # Uma lista para armazenar os itens relacionados a este pedido
                }
                pedidos.append(pedido)
            else:
                pedido = pedido_existente

            # Crie um registro para o item de pedido e hambugueres relacionados
            item_pedido = {
                'id': pedido_data[4],  # ID do item de pedido
                'burguer': {
                    'id': pedido_data[5],
                    'nome': pedido_data[6],
                    'descricao': pedido_data[7],
                    'preco': pedido_data[8],
                    'imagem_url': pedido_data[9]
                },
                'quantidade': pedido_data[10]
            }

            # Adicione o item de pedido à lista de itens do pedido
            pedido['itens'].append(item_pedido)

        conn.commit()
        conn.close()
        return pedidos
    except sqlite3.Error as e:
        print('Erro ao buscar pedidos realizados:', str(e))

    return []


@app.route('/obter_detalhes_pedido', methods=['GET'])
def obter_detalhes_pedido():
    pedido_id = request.args.get('pedido_id')
    # Suponha que você tenha uma função que retorne os detalhes do pedido com base no pedido_id
    pedido_detalhes = buscar_detalhes_pedido(pedido_id)

    if pedido_detalhes:
        # Renderize os detalhes do pedido em HTML
        html_detalhes_pedido = renderizar_detalhes_pedido(pedido_detalhes)
        return html_detalhes_pedido

    # Se o pedido não for encontrado, você pode retornar uma mensagem de erro
    return 'Pedido não encontrado', 404


def obter_imagem_url_pelo_nome_burguer(nome_burguer):
    try:
        conn = sqlite3.connect('app.db')  # Substitua pelo nome do seu banco de dados
        cursor = conn.cursor()

        # Consulta SQL para buscar a imagem_url do burguer com base no nome do burguer
        cursor.execute('SELECT imagem_url FROM burguers WHERE nome = ?', (nome_burguer,))

        # Obter o resultado da consulta
        resultado = cursor.fetchone()

        if resultado:
            imagem_url = resultado[0]
            return imagem_url
        else:
            return None

    except sqlite3.Error as e:
        print('Erro ao buscar imagem_url do Hambúrguer:', str(e))
        return None
    finally:
        conn.close()


def renderizar_detalhes_pedido(pedido_detalhes):
    # Use f-strings para formatação de string
    html = f'''
        <div class="pedido-details">
            <h2 class="pedido-title">Detalhes do Pedido</h2>
            <div class="pedido-info">
                <p>ID do Pedido: {pedido_detalhes["id"]}</p>
                <p>Cliente: {pedido_detalhes["cliente"]}</p> 
            </div>
            <h3 class="itens-title">Itens do Pedido</h3>
            <table class="itens-table">
                <thead>
                    <tr>
                        <th>Nome do burguer</th>
                        <th>Descrição</th>
                        <th>Preço Unitário</th>
                        <th>Quantidade</th>
                        <th>Imagem</th>
                    </tr>
                </thead>
                <tbody>
    '''
    # Use um loop for mais limpo e legível
    for item in pedido_detalhes['itens']:
        nome_burguer = item["nome"]
        imagem_url = obter_imagem_url_pelo_nome_burguer(nome_burguer)

        html += f'''
            <tr>
                <td>{item["nome"]}</td>
                <td>{item["descricao"]}</td>
                <td>R$ {item["preco_unitario"]}</td>
                <td>{item["quantidade"]}</td>
                <td><img src="{imagem_url}" alt="{nome_burguer}" class="burguer-image"></td>
            </tr>
        '''

    html += '</tbody></table>'
    html += '</div>'
    return html


# Função para buscar detalhes do pedido
def buscar_detalhes_pedido(pedido_id):
    try:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()

        # Consulta SQL para buscar detalhes do pedido com base no pedido_id
        cursor.execute('''
            SELECT 
                pedidos.id AS pedido_id, 
                pedidos.usuario_id, 
                pedidos.data_pedido, 
                pedidos.status, 
                itens_pedido.id AS item_pedido_id,
                burguers.id AS burguer_id,
                burguers.nome AS burguer_nome,
                burguers.descricao AS burguer_descricao,
                burguers.preco AS burguer_preco,
                burguers.imagem_url AS burguer_imagem_url,
                itens_pedido.quantidade
            FROM pedidos
            JOIN itens_pedido ON pedidos.id = itens_pedido.pedido_id
            JOIN burguers ON itens_pedido.burguer_id = burguers.id
            WHERE pedidos.id = ?
        ''', (pedido_id,))

        detalhes_pedido = {
            'itens': []
        }

        for row in cursor.fetchall():
            detalhes_pedido['id'] = row[0]
            detalhes_pedido['cliente'] = row[1]
            detalhes_pedido['endereco'] = row[5]
            detalhes_item = {
                'nome': row[6],
                'quantidade': row[10],
                'preco_unitario': row[8],
                'descricao': row[7]
            }
            detalhes_pedido['itens'].append(detalhes_item)

        conn.commit()
        conn.close()
        return detalhes_pedido

    except sqlite3.Error as e:
        print('Erro ao buscar detalhes do pedido:', str(e))
        return None


def obter_pedidos_por_usuario(usuario_id):
    try:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()

        # Consulta SQL para buscar detalhes dos pedidos do usuário com base no usuario_id
        cursor.execute('''
            SELECT 
                pedidos.id AS pedido_id, 
                pedidos.usuario_id, 
                pedidos.data_pedido, 
                pedidos.status, 
                itens_pedido.id AS item_pedido_id,
                burguers.id AS burguer_id,
                burguers.nome AS burguer_nome,
                burguers.descricao AS burguer_descricao,
                burguers.preco AS burguer_preco,
                burguers.imagem_url AS burguer_imagem_url,
                itens_pedido.quantidade
            FROM pedidos
            JOIN itens_pedido ON pedidos.id = itens_pedido.pedido_id
            JOIN burguers ON itens_pedido.burguer_id = burguers.id
            WHERE pedidos.usuario_id = ?
        ''', (usuario_id,))

        detalhes_pedidos = []
        pedido_grupo = {}  # Dicionário para agrupar pedidos pelo pedido_id

        for row in cursor.fetchall():
            pedido_id = row[0]

            # Se o pedido_id ainda não estiver no dicionário, cria uma entrada para ele
            if pedido_id not in pedido_grupo:
                pedido_grupo[pedido_id] = {
                    'pedido_id': pedido_id,
                    'usuario_id': row[1],
                    'data_pedido': row[2],
                    'status': row[3],
                    'itens_pedido': []
                }

            # Detalhes do item do pedido
            item_pedido = {
                'item_pedido_id': row[4],
                'burguer_id': row[5],
                'burguer_nome': row[6],
                'burguer_descricao': row[7],
                'burguer_preco': row[8],
                'burguer_imagem_url': row[9],
                'quantidade': row[10]
            }

            # Adicionar o item do pedido ao grupo do pedido correspondente
            pedido_grupo[pedido_id]['itens_pedido'].append(item_pedido)

        # Converter o dicionário de grupos de pedidos de volta em uma lista
        detalhes_pedidos = list(pedido_grupo.values())

        conn.commit()
        conn.close()
        return detalhes_pedidos

    except sqlite3.Error as e:
        print('Erro ao buscar detalhes dos pedidos do usuário:', str(e))
        return None


@app.route('/obter_pedidos_avaliados', methods=['GET'])
def obter_pedidos_avaliados():
    usuario_id = session['usuario_id']
    try:
        # Conecta ao banco de dados SQLite
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()

        # Consulte o banco de dados para obter todos os pedidos do usuário especificado
        cursor.execute('SELECT pedido_id, comentario, classificacao FROM avaliacoes WHERE usuario_id = ?',
                       (usuario_id,))

        # Recupera todos os pedidos do usuário
        pedidos = cursor.fetchall()
        print(pedidos)
        # Feche a conexão com o banco de dados
        conn.commit()
        conn.close()

        # Converta os resultados em um formato JSON e retorna como resposta
        return jsonify(pedidos)

    except sqlite3.Error as e:
        return jsonify({'mensagem': 'Erro no banco de dados'}), 500


@app.route('/listar_pedidos', methods=['GET'])
def listar_pedidos():
    # Recupere o 'usuario_id' do usuário logado da sessão
    usuario_id = session.get('usuario_id')

    if usuario_id is None:

        return redirect('/login')

    pedidos = obter_pedidos_por_usuario(usuario_id)
    print("Pedidos que vai: ", pedidos)

    return render_template('avaliar_item_pedido.html', pedidos=pedidos)


@app.route('/avaliar_item_pedido/<int:pedido_id>/<int:burguer_id>', methods=['GET', 'POST'])
def avaliar_item_pedido(pedido_id, burguer_id):
    # Verifica se o usuário está autenticado
    if 'usuario_id' not in session:
        flash('Faça o login para avaliar itens do pedido.', 'error')
        return redirect(url_for('login'))

    # Recupera informações do item do pedido
    item_pedido = obter_item_pedido_por_ids(pedido_id, burguer_id)

    # Verifique se o item do pedido existe e pertence ao usuário logado
    if not item_pedido or item_pedido['usuario_id'] != session['usuario_id']:
        flash('Item do pedido não encontrado ou não autorizado para avaliação.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        classificacao = int(request.form.get('classificacao'))
        comentario = request.form.get('comentario')

        # Salva a avaliação do item do pedido no banco de dados
        salvar_avaliacao_item_pedido(pedido_id, burguer_id, classificacao, comentario)

        flash('Item do pedido avaliado com sucesso.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('avaliar_item_pedido.html', item_pedido=item_pedido)


@app.route('/inserir_avaliacao', methods=['POST'])
def inserir_avaliacao():
    data = request.json
    print(data)
    pedido_id = data.get('pedido_id')
    classificacao = data.get('classificacao')
    comentario = data.get('comentario')
    usuario_id = data.get('usuario_id')

    if pedido_id is not None and comentario is not None:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO avaliacoes (pedido_id, classificacao, comentario, usuario_id) VALUES (?, ?, ?,?)',
                       (pedido_id, classificacao, comentario, usuario_id))
        conn.commit()
        conn.close()

        # Responda com um JSON para indicar o sucesso
        return jsonify({'message': 'Avaliação inserida com sucesso'}), 200
    else:
        # Responda com um JSON para indicar um erro
        return jsonify({'error': 'Dados de avaliação inválidos'}), 400


@app.route('/avaliacoes_pedido/<int:pedido_id>/<int:usuario_id>')
def obter_avaliacoes_pedido(pedido_id, usuario_id):
    conn = sqlite3.connect('app.db')
    print("Usuario ID:", usuario_id)
    cursor = conn.cursor()
    cursor.execute('SELECT classificacao, comentario FROM avaliacoes WHERE pedido_id = ? AND usuario_id = ?',
                   (pedido_id, usuario_id,))
    avaliacoes = cursor.fetchall()
    conn.commit()
    conn.close()
    return jsonify(avaliacoes)


@app.route('/obter_usuario_id/<int:pedido_id>', methods=['GET'])
def obter_usuario_id(pedido_id):
    try:
        # Consulte o banco de dados para obter o usuario_id com base no pedido_id
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute('SELECT usuario_id FROM pedidos WHERE id = ?', (pedido_id,))
        usuario_info = cursor.fetchone()
        print(usuario_info)
        conn.commit()
        conn.close()

        if usuario_info:
            return jsonify({'usuario_id': usuario_info[0]})
        else:
            return jsonify({'mensagem': 'Pedido não encontrado'}), 404
    except sqlite3.Error as e:
        return jsonify({'mensagem': 'Erro no banco de dados'}), 500


@app.route('/verificar_avaliacao/<int:pedido_id>', methods=['GET'])
def verificar_avaliacao(pedido_id):
    try:
        # Consulta SQL para verificar a avaliação com base no pedido_id
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id ,classificacao, comentario FROM avaliacoes WHERE pedido_id = ?', (pedido_id,))
        resultado = cursor.fetchone()

        conn.commit()
        conn.close()

        if resultado:
            # Se houver uma avaliação, retorna a classificação e o comentário
            id, classificacao, comentario = resultado
            print(resultado)
            return jsonify({'avaliacao_id': id, 'classificacao': classificacao, 'comentario': comentario})
        else:
            # Se não houver uma avaliação, retorne None (ou um valor apropriado)
            return jsonify(None)
    except sqlite3.Error as e:
        # Lida com erros de banco de dados
        return jsonify({'error': str(e)})


@app.route('/atualizar_avaliacao/<int:avaliacao_id>', methods=['PUT'])
def atualizar_avaliacao(avaliacao_id):
    try:
        # Verifique se a avaliação com o ID especificado existe
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM avaliacoes WHERE id = ?', (avaliacao_id,))
        avaliacao = cursor.fetchone()
        print(avaliacao)

        if not avaliacao:
            return jsonify({'error': 'Avaliação não encontrada'}), 404

        # Recupere os novos dados da avaliação do corpo da solicitação
        novo_classificacao = request.json.get('classificacao')
        novo_comentario = request.json.get('comentario')
        print(novo_classificacao)
        print(novo_comentario)

        # Atualize os dados da avaliação no banco de dados
        cursor.execute('''
            UPDATE avaliacoes
            SET classificacao = ?, comentario = ?
            WHERE id = ?
        ''', (novo_classificacao, novo_comentario, avaliacao_id))

        conn.commit()
        conn.close()

        return jsonify({'message': 'Avaliação atualizada com sucesso'})

    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
