import discord
from discord.ext import commands
from discord import app_commands, File, ButtonStyle, TextStyle
from discord.ui import Button, View, Modal, Select, TextInput
import pandas as pd
from pymongo import MongoClient
import os
from dotenv import load_dotenv 
import io
import numpy as np

import trabalho

load_dotenv()
TOKEN = os.getenv('discord_token')
MONGO_URI = os.getenv('MONGO_URI')

if not TOKEN or not MONGO_URI:
    print("ERRO: TOKEN ou MONGO_URI não encontrados no .env. Verifique o arquivo.")
    exit()

try:
    client = MongoClient(MONGO_URI)
    client.admin.command('ping')
    db = client['empresa_ti']
    collection_vendas = db['vendas']
    collection_usuarios = db['usuarios']
    print("Conexão com MongoDB Atlas estabelecida com sucesso!")
except Exception as e:
    print(f"ERRO: Não foi possível conectar ao MongoDB. {e}")
    exit()

df_vendas_cache = None

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

usuarios_logados = set()


async def carregar_dados_do_mongo():
    global df_vendas_cache
    print("Carregando dados do MongoDB para o cache...")
    try:
        cursor = collection_vendas.find({})
        df = pd.DataFrame(list(cursor))
        
        df.rename(columns={
            'DATETIME': 'Data_Venda',
            'MONEY': 'Preco_Venda',
            'PRODUCTS': 'Produto',
            'CASH_TYPE': 'Categoria'
        }, inplace=True)
        
        df['Data_Venda'] = pd.to_datetime(df['Data_Venda'])
        
        df['Quantidade'] = 1
        
        custo_aleatorio_percent = np.random.uniform(0.20, 0.60, size=len(df))
        df['Custo_Unitario'] = (df['Preco_Venda'] * custo_aleatorio_percent).round(2)
        
        df['Total_Venda'] = df['Preco_Venda'] * df['Quantidade']
        df['Custo_Total'] = df['Custo_Unitario'] * df['Quantidade']
        df['Lucro_Bruto'] = df['Total_Venda'] - df['Custo_Total']
        
        df_vendas_cache = df
        print(f"Cache atualizado com {len(df_vendas_cache)} linhas (com custo aleatório).")
        return df_vendas_cache
    except Exception as e:
        print(f"Erro ao carregar dados do Mongo: {e}")
        return None


class ModalRegistro(Modal, title="Registro de Novo Usuário"):
    login = TextInput(label="Seu Login (ou email)", placeholder="ex: usuario@dominio.com", required=True)
    senha = TextInput(label="Sua Senha", placeholder="Crie uma senha segura", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        login = self.login.value
        senha = self.senha.value 
        try:
            collection_usuarios.insert_one({
                'user_id': user_id, 'login': login, 'senha': senha, 'discord_name': interaction.user.name
            })
            await interaction.response.send_message(
                f"✅ Usuário '{login}' registrado com sucesso! Agora clique em 'Login' para entrar.", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Erro ao registrar. Você já possui uma conta?", ephemeral=True
            )

class ModalLogin(Modal, title="Login no Sistema"):
    login = TextInput(label="Seu Login", required=True)
    senha = TextInput(label="Sua Senha", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        login = self.login.value
        senha = self.senha.value
        
        usuario_db = collection_usuarios.find_one({
            'user_id': user_id, 'login': login, 'senha': senha
        })
        
        if usuario_db:
            usuarios_logados.add(user_id) 
            await interaction.response.edit_message(
                content=f"Login bem-sucedido, {interaction.user.mention}! O que deseja fazer?",
                view=ViewMenuPrincipal(), embed=None 
            )
        else:
            await interaction.response.send_message(
                "❌ Login ou senha incorretos. Tente novamente ou clique em 'Registro'.", ephemeral=True
            )

class ModalAnaliseABC(Modal, title="1.6 Análise ABC"):
    percentual = TextInput(label="Percentual de Faturamento (%)", placeholder="Ex: 80 (para Categoria A)", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            percentual = float(self.percentual.value)
            if not (0 < percentual <= 100):
                raise ValueError("Percentual fora do range")

            await interaction.response.edit_message(content="Processando Análise ABC...", view=None)
            
            mensagem_texto = trabalho.inserir_analise_abc(df_vendas_cache, percentual) 
            
            await interaction.channel.send(content=mensagem_texto)
            await interaction.delete_original_response()
            await interaction.followup.send("Análise enviada. Escolha a próxima:", view=ViewMenuDadosColetados(), ephemeral=True)

        except ValueError:
            await interaction.response.send_message("Erro: O valor deve ser um número entre 1 e 100. Tente novamente.", ephemeral=True)

class ModalSimulacaoSaida(Modal, title="1.7 Simulação de Saída de Estoque"):
    produto = TextInput(label="Nome Exato do Produto", placeholder="Ex: GPU RTX 4080", required=True)
    estoque_atual = TextInput(label="Quantidade em Estoque Atual", placeholder="Ex: 50", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            produto = self.produto.value
            estoque = int(self.estoque_atual.value)

            await interaction.response.edit_message(content="Processando simulação...", view=None)
            
            mensagem_texto = trabalho.inserir_simulacao_saida_estoque(df_vendas_cache, produto, estoque)
            
            await interaction.channel.send(content=mensagem_texto)
            await interaction.delete_original_response()
            await interaction.followup.send("Simulação enviada. Escolha a próxima:", view=ViewMenuDadosColetados(), ephemeral=True)
            
        except ValueError:
            await interaction.response.send_message("Erro: Estoque deve ser um número. Tente novamente.", ephemeral=True)
        except Exception as e:
             await interaction.response.send_message(f"Erro: {e}", ephemeral=True)

class ModalPrevisaoDemanda(Modal, title="2.1 Prever Demanda (Simulação)"):
    fator_crescimento = TextInput(label="Fator de Crescimento (%)", placeholder="Ex: 10 (para 10%)", required=True)
    estoque_atual = TextInput(label="Quantidade em Estoque Atual", placeholder="Ex: 500", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            fator = float(self.fator_crescimento.value)
            estoque = int(self.estoque_atual.value)
            
            await interaction.response.edit_message(content="Processando simulação...", view=None)
            
            mensagem_texto = trabalho.inserir_previsao_demanda(df_vendas_cache, fator, estoque)
            
            await interaction.channel.send(content=mensagem_texto)
            await interaction.delete_original_response()
            await interaction.followup.send("Simulação enviada. Escolha a próxima:", view=ViewMenuDadosInseridos(), ephemeral=True)
            
        except ValueError:
            await interaction.response.send_message("Erro: Os valores devem ser números. Tente novamente.", ephemeral=True)

class ModalCalcularLucro(Modal, title="2.2 Calcular Lucro (Simulação)"):
    custo = TextInput(label="Custo de Compra (R$)", placeholder="Ex: 150.50", required=True)
    preco_venda = TextInput(label="Preço de Venda (R$)", placeholder="Ex: 220.00", required=True)
    quantidade = TextInput(label="Quantidade Vendida", placeholder="Ex: 10", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            custo = float(self.custo.value)
            preco_venda = float(self.preco_venda.value)
            quantidade = int(self.quantidade.value)

            await interaction.response.edit_message(content="Calculando...", view=None)

            mensagem_texto = trabalho.inserir_calcular_lucro(custo, preco_venda, quantidade)
            
            await interaction.channel.send(content=mensagem_texto)
            await interaction.delete_original_response()
            await interaction.followup.send("Cálculo enviado. Escolha a próxima simulação:", view=ViewMenuDadosInseridos(), ephemeral=True)

        except ValueError:
            await interaction.response.send_message("Erro: Os valores de Custo/Preço/Quantidade devem ser números. Tente novamente.", ephemeral=True)

class ModalOtimizarPreco(Modal, title="2.3 Otimizar Preço (Simulação)"):
    custo = TextInput(label="Custo de Compra (R$)", placeholder="Ex: 150.50", required=True)
    margem = TextInput(label="Margem de Lucro Desejada (%)", placeholder="Ex: 50 (para 50%)", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            custo = float(self.custo.value)
            margem = float(self.margem.value)

            await interaction.response.edit_message(content="Calculando...", view=None)
            
            mensagem_texto = trabalho.inserir_otimizar_preco(custo, margem)
            
            await interaction.channel.send(content=mensagem_texto)
            await interaction.delete_original_response()
            await interaction.followup.send("Cálculo enviado. Escolha a próxima simulação:", view=ViewMenuDadosInseridos(), ephemeral=True)

        except ValueError:
            await interaction.response.send_message("Erro: Os valores devem ser números. Tente novamente.", ephemeral=True)

class ModalPontoEquilibrio(Modal, title="2.4 Ponto de Equilíbrio (Simulação)"):
    custo_fixo = TextInput(label="Custos Fixos Mensais (R$)", placeholder="Ex: 5000 (Aluguel, Salários)", required=True)
    custo_variavel = TextInput(label="Custo Variável por Unidade (R$)", placeholder="Ex: 150 (Custo do produto)", required=True)
    preco_venda = TextInput(label="Preço de Venda por Unidade (R$)", placeholder="Ex: 350", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            custo_fixo = float(self.custo_fixo.value)
            custo_variavel = float(self.custo_variavel.value)
            preco_venda = float(self.preco_venda.value)

            await interaction.response.edit_message(content="Calculando Ponto de Equilíbrio...", view=None)
            
            mensagem_texto = trabalho.simular_ponto_equilibrio(custo_fixo, custo_variavel, preco_venda)
            
            await interaction.channel.send(content=mensagem_texto)
            await interaction.delete_original_response()
            await interaction.followup.send("Análise enviada. Escolha a próxima simulação:", view=ViewMenuDadosInseridos(), ephemeral=True)

        except ValueError:
            await interaction.response.send_message("Erro: Todos os valores devem ser números. Tente novamente.", ephemeral=True)

class ModalCompararProdutos(Modal, title="2.5 Comparar Lucratividade (Simulação)"):
    preco_venda = TextInput(label="Preço de Venda Comum (R$)", placeholder="Ex: 350.00", required=True)
    nome_a = TextInput(label="Nome Produto A", placeholder="Ex: CPU X", required=True)
    custo_a = TextInput(label="Custo Produto A (R$)", placeholder="Ex: 150.00", required=True)
    nome_b = TextInput(label="Nome Produto B", placeholder="Ex: CPU Y", required=True)
    custo_b = TextInput(label="Custo Produto B (R$)", placeholder="Ex: 170.00", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            preco_venda = float(self.preco_venda.value)
            custo_a = float(self.custo_a.value)
            custo_b = float(self.custo_b.value)

            await interaction.response.edit_message(content="Comparando produtos...", view=None)
            
            mensagem_texto = trabalho.simular_comparar_produtos(self.nome_a.value, custo_a, self.nome_b.value, custo_b, preco_venda)
            
            await interaction.channel.send(content=mensagem_texto)
            await interaction.delete_original_response()
            await interaction.followup.send("Comparação enviada. Escolha a próxima simulação:", view=ViewMenuDadosInseridos(), ephemeral=True)

        except ValueError:
            await interaction.response.send_message("Erro: Custo e Preço devem ser números. Tente novamente.", ephemeral=True)


class ViewPainelLogin(View):
    def __init__(self):
        super().__init__(timeout=None) 

    @discord.ui.button(label="Login", style=ButtonStyle.green, custom_id="login_button")
    async def login_callback(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(ModalLogin())

    @discord.ui.button(label="Registro", style=ButtonStyle.blurple, custom_id="register_button")
    async def register_callback(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(ModalRegistro())

class ViewMenuPrincipal(View):
    def __init__(self):
        super().__init__(timeout=180) 

    @discord.ui.select(
        placeholder="Selecione uma opção...",
        options=[
            discord.SelectOption(label="1. Dados Coletados", value="1", description="Ver análises prontas e gráficos."),
            discord.SelectOption(label="2. Dados Inseridos", value="2", description="Simular cenários de negócio."),
            discord.SelectOption(label="3. Deslogar", value="3", description="Encerrar sua sessão."),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: Select):
        valor = select.values[0]
        
        if valor == "1":
            await interaction.response.edit_message(
                content="Opção 1 selecionada. Escolha a análise:",
                view=ViewMenuDadosColetados()
            )
        elif valor == "2":
            await interaction.response.edit_message(
                content="Opção 2 selecionada. Escolha a simulação:",
                view=ViewMenuDadosInseridos()
            )
        elif valor == "3":
            if interaction.user.id in usuarios_logados:
                usuarios_logados.remove(interaction.user.id)
            
            await interaction.response.edit_message(content="Deslogando...", view=None)
            await interaction.delete_original_response()
            await interaction.followup.send("Você foi desconectado.", ephemeral=True, delete_after=3)

class ViewMenuDadosColetados(View):
    def __init__(self):
        super().__init__(timeout=180)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in usuarios_logados:
            await interaction.response.send_message("Sua sessão expirou. Por favor, use `/login` novamente.", ephemeral=True)
            return False
        return True

    @discord.ui.select(
        placeholder="Selecione a análise...",
        options=[
            discord.SelectOption(label="1.1 Lucro Anual", value="1.1"),
            discord.SelectOption(label="1.2 Lucro Mensal", value="1.2"),
            discord.SelectOption(label="1.3 Margem por Produto", value="1.3"),
            discord.SelectOption(label="1.4 Previsão de Estoque", value="1.4"),
            discord.SelectOption(label="1.5 Ranking de Lucratividade", value="1.5"),
            discord.SelectOption(label="1.6 Análise ABC", value="1.6"),
            discord.SelectOption(label="1.7 Simulação de Saída", value="1.7"),
            discord.SelectOption(label="1.8 Nuvem de Palavras", value="1.8"),
            discord.SelectOption(label="6. Voltar", value="6", emoji="⬅️"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: Select):
        global df_vendas_cache
        if df_vendas_cache is None:
            await carregar_dados_do_mongo()
            
        valor = select.values[0]

        if valor == "6":
            await interaction.response.edit_message(
                content="O que deseja fazer?",
                view=ViewMenuPrincipal()
            )
            return

        if valor == "1.6":
            await interaction.response.send_modal(ModalAnaliseABC())
            return 
        elif valor == "1.7":
            await interaction.response.send_modal(ModalSimulacaoSaida())
            return 

        await interaction.response.edit_message(
            content=f"Processando Análise {valor}. Por favor, aguarde...",
            view=None
        )

        buffer_imagem = None
        mensagem_texto = ""

        if valor == "1.1":
            buffer_imagem, mensagem_texto = trabalho.analise_lucro_anual(df_vendas_cache)
        elif valor == "1.2":
            buffer_imagem, mensagem_texto = trabalho.analise_lucro_mensal(df_vendas_cache)
        elif valor == "1.3":
            buffer_imagem, mensagem_texto = trabalho.analise_lucro_sobre_produto(df_vendas_cache)
        elif valor == "1.4":
            buffer_imagem, mensagem_texto = trabalho.previsao_de_estoque(df_vendas_cache)
        elif valor == "1.5":
            buffer_imagem, mensagem_texto = trabalho.analise_produtos_mais_lucrativos(df_vendas_cache)
        elif valor == "1.8":
            buffer_imagem, mensagem_texto = trabalho.analise_nuvem_lucro(df_vendas_cache)

        if buffer_imagem is None and mensagem_texto:
            await interaction.channel.send(content=mensagem_texto) 
        else:
            await interaction.channel.send(content=mensagem_texto)
            await interaction.channel.send(file=File(buffer_imagem, filename=f'analise_{valor}.png'))
        
        await interaction.delete_original_response()

        await interaction.followup.send(
            content="Análise pública enviada. Escolha a próxima análise ou volte:",
            view=ViewMenuDadosColetados(), 
            ephemeral=True
        )

class ViewMenuDadosInseridos(View):
    def __init__(self):
        super().__init__(timeout=180)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in usuarios_logados:
            await interaction.response.send_message("Sua sessão expirou. Por favor, use `/login` novamente.", ephemeral=True)
            return False
        return True

    @discord.ui.select(
        placeholder="Selecione a simulação...",
        options=[
            discord.SelectOption(label="2.1 Prever Demanda (Histórico)", value="2.1"),
            discord.SelectOption(label="2.2 Calcular Lucro (Simples)", value="2.2"),
            discord.SelectOption(label="2.3 Otimizar Preço (Simples)", value="2.3"),
            discord.SelectOption(label="2.4 Ponto de Equilíbrio (Breakeven)", value="2.4"),
            discord.SelectOption(label="2.5 Comparar Lucro de Produtos", value="2.5"),
            discord.SelectOption(label="6. Voltar", value="6", emoji="⬅️"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: Select):
        global df_vendas_cache
        if df_vendas_cache is None:
            await carregar_dados_do_mongo()
            
        valor = select.values[0]

        if valor == "6":
            await interaction.response.edit_message(
                content="O que deseja fazer?",
                view=ViewMenuPrincipal()
            )
            return

        if valor == "2.1":
            await interaction.response.send_modal(ModalPrevisaoDemanda())
        elif valor == "2.2":
            await interaction.response.send_modal(ModalCalcularLucro())
        elif valor == "2.3":
            await interaction.response.send_modal(ModalOtimizarPreco())
        elif valor == "2.4":
            await interaction.response.send_modal(ModalPontoEquilibrio())
        elif valor == "2.5":
            await interaction.response.send_modal(ModalCompararProdutos())


@bot.event
async def on_ready():
    await carregar_dados_do_mongo()
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos.")
    except Exception as e:
        print(f"Erro ao sincronizar: {e}")
    
    print(f'Bot conectado como {bot.user}')

@bot.tree.command(name="login", description="Mostra o painel de Login e Registro.")
async def login_panel(interaction: discord.Interaction):
    
    embed = discord.Embed(
        title="📊 Painel de Análise de TI",
        description="Bem-vindo ao sistema de análise de dados da Consultoria de TI.\n\n"
                    "Para acessar os relatórios e previsões, você precisa estar autenticado.",
        color=discord.Color.blue()
    )
    embed.add_field(name="Login", value="Se você já possui uma conta, clique abaixo para entrar.")
    embed.add_field(name="Registro", value="Se é seu primeiro acesso, registre-se gratuitamente.")
    
    await interaction.response.send_message(embed=embed, view=ViewPainelLogin(), ephemeral=True)

@bot.tree.command(name="recarregar_dados", description="[Admin] Força o recarregamento dos dados do MongoDB.")
@app_commands.default_permissions(administrator=True) 
async def recarregar_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await carregar_dados_do_mongo()
    await interaction.followup.send("Cache de dados atualizado com sucesso a partir do MongoDB.", ephemeral=True)


if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        print("Erro: Token do Discord inválido.")
    except Exception as e:
        print(f"Erro geral: {e}")