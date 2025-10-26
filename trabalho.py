import pandas as pd
import numpy as np
from datetime import timedelta, date
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression 
import time 

# =================================================================
# 0. GERAÇÃO E TRATAMENTO DOS DADOS FALSOS (DADOS COLETADOS)
# =================================================================

# 1. Definir Produtos e Custos Fixos
produtos_info = {
    'Produto A (Eletrônico)': {'Categoria': 'Eletrônico', 'Custo': 150.00},
    'Produto B (Alimento)': {'Categoria': 'Alimento', 'Custo': 5.00},
    'Produto C (Vestuário)': {'Categoria': 'Vestuário', 'Custo': 30.00},
    'Produto D (Eletrônico)': {'Categoria': 'Eletrônico', 'Custo': 500.00},
    'Produto E (Alimento)': {'Categoria': 'Alimento', 'Custo': 1.50},
    'Produto F (Vestuário)': {'Categoria': 'Vestuário', 'Custo': 80.00},
}
lista_produtos = list(produtos_info.keys())

# Configurações de Simulação
N_TRANSACOES = 5000
DATA_INICIO = date(2024, 1, 1)
DATA_FIM = date(2025, 1, 1)
DIAS = (DATA_FIM - DATA_INICIO).days

# Geração de Dados Aleatórios
datas = [DATA_INICIO + timedelta(days=np.random.randint(DIAS)) for _ in range(N_TRANSACOES)]
# Probabilidade de venda (B e E vendem mais, D vende menos)
produtos_vendidos = np.random.choice(lista_produtos, N_TRANSACOES, 
                                     p=[0.10, 0.30, 0.20, 0.05, 0.25, 0.10])
quantidades = np.random.randint(1, 10, N_TRANSACOES)

custos_unitarios = []
precos_venda = []
for i, produto in enumerate(produtos_vendidos):
    custo = produtos_info[produto]['Custo']
    # Se for eletrônico, a quantidade é menor (realismo)
    if 'Eletrônico' in produto:
        quantidades[i] = np.random.randint(1, 3) 
    
    # Margem de lucro aleatória (entre 10% e 80%)
    margem = np.random.uniform(0.1, 0.8)
    preco = custo * (1 + margem)
    
    custos_unitarios.append(custo)
    # Simula uma pequena variação no preço de venda para alguns produtos
    precos_venda.append(round(preco * np.random.uniform(0.98, 1.02), 2)) 

# Criação do DataFrame
df_vendas = pd.DataFrame({
    'ID_Venda': np.arange(1, N_TRANSACOES + 1),
    'Data_Venda': datas,
    'Produto': produtos_vendidos, # Coluna corrigida
    'Custo_Unitario': custos_unitarios,
    'Preco_Venda': precos_venda,
    'Quantidade': quantidades
})

# =================================================================
# CORREÇÃO CRÍTICA: GARANTE QUE A COLUNA SEJA UM TIPO DATETIME VÁLIDO
df_vendas['Data_Venda'] = pd.to_datetime(df_vendas['Data_Venda'])
# =================================================================

# Adicionar Categoria
df_vendas['Categoria'] = df_vendas['Produto'].apply(lambda x: produtos_info[x]['Categoria'])

# --- 5. Cálculo de Métricas (Dados "Tratados" e prontos para uso) ---
df_vendas['Total_Venda'] = df_vendas['Preco_Venda'] * df_vendas['Quantidade']
df_vendas['Custo_Total'] = df_vendas['Custo_Unitario'] * df_vendas['Quantidade']
df_vendas['Lucro_Bruto'] = df_vendas['Total_Venda'] - df_vendas['Custo_Total']

# =================================================================
# 1. FUNÇÕES DE EXIBIÇÃO E CÁLCULO
# =================================================================

def limpar_tela():
    """Simula a limpeza do console para melhor UX."""
    print("\n" * 50) 

def exibir_grafico(df, titulo="Gráfico de Análise", x_label="Eixo X", y_label="Eixo Y"):
    """Exibe um gráfico e espera o usuário pressionar Enter."""
    print(f"\n--- {titulo} ---")
    
    # Tenta mostrar o gráfico. Em ambientes sem suporte, mostra uma mensagem.
    try:
        plt.show() 
    except Exception as e:
        print(f"[Simulação de Gráfico: Plote real será exibido em um ambiente adequado (IDE/Jupyter). Erro: {e}]")
        
    print(f"\n[Fim da Análise de {titulo}. Pressione Enter para voltar ao menu.]")
    input()


# -----------------------------------------------------------------
# 1.1 Funções para o Menu 1: Dados Coletados (Análises Prontas)
# -----------------------------------------------------------------

def analise_lucro_anual(df):
    """Opção 1.1: Lucro Anual Total."""
    limpar_tela()
    
    lucro_total = df['Lucro_Bruto'].sum()
    
    print("--- 1.1 Lucro Anual Total (2024) ---")
    print(f"\nO Lucro Bruto Total acumulado no período é de: R$ {lucro_total:,.2f}")
    
    # Geração de Gráfico (Exemplo: Lucro por Mês)
    df_mensal = df.set_index('Data_Venda').resample('ME')['Lucro_Bruto'].sum()
    
    plt.figure(figsize=(10, 6))
    df_mensal.plot(kind='line', marker='o', color='green')
    plt.title('Tendência de Lucro Mensal (Gráfico)')
    plt.xlabel('Mês')
    plt.ylabel('Lucro Bruto (R$)')
    plt.grid(True)
    plt.tight_layout()
    exibir_grafico(plt, "Lucro Anual Total")


def analise_lucro_mensal(df):
    """Opção 1.2: Lucro Médio Mensal."""
    limpar_tela()
    print("--- 1.2 Lucro Médio Mensal ---")
    
    df_mensal = df.set_index('Data_Venda').resample('ME')['Lucro_Bruto'].sum()
    lucro_medio_mensal = df_mensal.mean()
    
    print(f"\nLucro Bruto Médio Mensal: R$ {lucro_medio_mensal:,.2f}")
    print("\nOs meses com melhor desempenho foram:")
    # CORREÇÃO: Usando .to_string() para formatar a saída e remover o cabeçalho pandas
    print(df_mensal.nlargest(3).apply(lambda x: f"R$ {x:,.2f}").to_string())
    
    # Geração de Gráfico (Top 5 Produtos em Lucro)
    df_lucro_produto = df.groupby('Produto')['Lucro_Bruto'].sum().sort_values(ascending=False).head(5)
    
    plt.figure(figsize=(10, 6))
    df_lucro_produto.plot(kind='bar', color='blue')
    plt.title('Top 5 Produtos por Lucro Bruto (Gráfico)')
    plt.xlabel('Produto')
    plt.ylabel('Lucro Bruto (R$)')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    exibir_grafico(plt, "Lucro Médio Mensal")


def analise_lucro_sobre_produto(df):
    """Opção 1.3: Lucro sobre Produto (Margem Média)."""
    limpar_tela()
    print("--- 1.3 Lucro sobre Produto (Margem Média) ---")
    
    # Calcular a Margem de Lucro Bruto (MLB) para cada transação: (Preco_Venda - Custo_Unitario) / Preco_Venda
    df['Margem_Lucro'] = (df['Preco_Venda'] - df['Custo_Unitario']) / df['Preco_Venda']
    
    # Agrupar e calcular a margem média por produto
    margens_medias = df.groupby('Produto')['Margem_Lucro'].mean().sort_values(ascending=False)
    
    print("\nMargem de Lucro Média por Produto:")
    # CORREÇÃO: Usando .to_string() para formatar a saída e remover o cabeçalho pandas
    print(margens_medias.apply(lambda x: f"{x * 100:.2f}%").to_string())
    
    # Geração de Gráfico
    plt.figure(figsize=(10, 6))
    (margens_medias * 100).plot(kind='barh', color='darkred')
    plt.title('Margem de Lucro Média por Produto (Gráfico)')
    plt.xlabel('Margem de Lucro Média (%)')
    plt.ylabel('Produto')
    plt.tight_layout()
    exibir_grafico(plt, "Lucro sobre Produto")


def previsao_de_estoque(df):
    """Opção 1.4: Previsão de Demanda (usando Scikit-learn)."""
    limpar_tela()
    print("--- 1.4 Previsão de Estoque (Demanda do Próximo Mês) ---")
    
    # Preparar dados para o modelo de regressão (simples: dia do ano vs. quantidade)
    df['Dia_do_Ano'] = df['Data_Venda'].apply(lambda x: x.timetuple().tm_yday)
    
    # Usaremos um produto específico (Produto B) para a previsão
    df_prod_b = df[df['Produto'] == 'Produto B (Alimento)']
    
    # Modelo de Regressão Linear Simples para simular tendência
    X = df_prod_b[['Dia_do_Ano']]
    y = df_prod_b['Quantidade']
    
    # Treinamento
    model = LinearRegression()
    model.fit(X, y)
    
    # CORREÇÃO DO WARNING: Passa o valor futuro como um DataFrame com nome de feature
    dia_futuro = 380
    X_futuro = pd.DataFrame({'Dia_do_Ano': [dia_futuro]})
    previsao_qty = model.predict(X_futuro)[0]
    
    print(f"\nBaseado no histórico do 'Produto B (Alimento)':")
    print(f"Previsão de Quantidade Média de Venda para o dia {dia_futuro} (início de 2025): {max(1, round(previsao_qty)):.0f} unidades.")
    
    # Geração de Gráfico: Comparação da Venda Real vs. Previsão
    df_mensal = df_prod_b.set_index('Data_Venda').resample('ME')['Quantidade'].sum()
    
    plt.figure(figsize=(10, 6))
    df_mensal.plot(kind='bar', color='orange')
    plt.title('Vendas Mensais de Produto B vs. Projeção (Gráfico)')
    plt.xlabel('Mês')
    plt.ylabel('Quantidade Vendida')
    # Projeta a venda total para o mês (média diária * 30 dias)
    plt.axhline(previsao_qty * 30, color='red', linestyle='--', label=f'Projeção Mês Futuro ({previsao_qty * 30:.0f} unid.)')
    plt.legend()
    plt.tight_layout()
    exibir_grafico(plt, "Previsão de Estoque")


def analise_produtos_mais_lucrativos(df):
    """Opção 1.5: Listar os produtos mais lucrativos."""
    limpar_tela()
    print("--- 1.5 Ranking de Lucratividade por Categoria ---")

    # Agrupar Lucro por Categoria
    lucro_por_categoria = df.groupby('Categoria')['Lucro_Bruto'].sum().sort_values(ascending=False)
    
    print("\nLucro Bruto Total por Categoria:")
    # CORREÇÃO: Usando .to_string() para formatar a saída e remover o cabeçalho pandas
    print(lucro_por_categoria.apply(lambda x: f"R$ {x:,.2f}").to_string())
    
    # O item que mais gerou lucro
    produto_mais_lucrativo = df.groupby('Produto')['Lucro_Bruto'].sum().idxmax()
    lucro_max = df.groupby('Produto')['Lucro_Bruto'].sum().max()
    print(f"\nO item que mais gerou lucro total é: {produto_mais_lucrativo} (R$ {lucro_max:,.2f})")

    # Geração de Gráfico
    plt.figure(figsize=(8, 5))
    lucro_por_categoria.plot(kind='pie', autopct='%1.1f%%', startangle=90, colors=['#ff9999','#66b3ff','#99ff99'])
    plt.title('Distribuição Percentual do Lucro Bruto por Categoria (Gráfico)')
    plt.ylabel('')
    plt.tight_layout()
    exibir_grafico(plt, "Produtos Mais Lucrativos")


# -----------------------------------------------------------------
# 1.2 Funções para o Menu 2: Dados Inseridos (Interativo)
# -----------------------------------------------------------------

def inserir_previsao_demanda():
    """Opção 2.1: Prever Demanda (Interativo Simples)."""
    limpar_tela()
    print("--- 2.1 Previsão de Demanda (Simples) ---")
    
    # O usuário insere um fator de crescimento para a demanda
    try:
        fator_crescimento = float(input("Insira o Fator de Crescimento da Demanda (%) para o próximo mês (ex: 10 para 10%): "))
        estoque_atual = int(input("Insira a Quantidade Atual em Estoque: "))
    except ValueError:
        print("\nErro: Insira apenas números válidos.")
        input("Pressione Enter para voltar.")
        return
    
    # Calcula a média de vendas diárias do DF geral para simulação
    dias_no_ano = 365
    venda_diaria_media = df_vendas['Quantidade'].sum() / dias_no_ano
    
    # Aplica o fator de crescimento na média
    nova_venda_diaria = venda_diaria_media * (1 + fator_crescimento / 100)
    
    print("\n--- Resultado da Simulação ---")
    print(f"Média de Vendas Diárias (Base Histórica): {venda_diaria_media:.2f} unidades.")
    print(f"Projeção de Nova Média Diária (com {fator_crescimento:.0f}% de Crescimento): {nova_venda_diaria:.2f} unidades.")
    
    # Estima quantos dias o estoque atual duraria
    dias_restantes = estoque_atual / nova_venda_diaria if nova_venda_diaria > 0 else "Indefinido (Venda 0)"
    
    print(f"Se o crescimento for atingido, seu estoque atual de {estoque_atual} unidades durará: {dias_restantes:.1f} dias.")
    
    input("\nPressione Enter para voltar.")


def inserir_calcular_lucro():
    """Opção 2.2: Calcular Lucro (Interativo)."""
    limpar_tela()
    print("--- 2.2 Calcular Lucro (Valores Manuais) ---")
    try:
        custo = float(input("Insira o Custo de Compra Unitário (R$): "))
        preco_venda = float(input("Insira o Preço de Venda Unitário (R$): "))
        quantidade = int(input("Insira a Quantidade Vendida: "))
    except ValueError:
        print("\nErro: Insira apenas números válidos.")
        input("Pressione Enter para voltar.")
        return
        
    if preco_venda < custo:
        print("\nAVISO: O Preço de Venda é menor que o Custo! Você terá prejuízo.")
        
    lucro_unitario = preco_venda - custo
    lucro_total = lucro_unitario * quantidade
    
    print("\n--- Resultado do Cálculo ---")
    print(f"Lucro Unitário: R$ {lucro_unitario:,.2f}")
    print(f"Lucro Total (em {quantidade} unidades): R$ {lucro_total:,.2f}")
    
    input("\nPressione Enter para voltar.")


def inserir_otimizar_preco():
    """Opção 2.3: Otimizar Preço (Margem Desejada)."""
    limpar_tela()
    print("--- 2.3 Otimizar Preço (Margem de Lucro Desejada) ---")
    
    try:
        custo = float(input("Insira o Custo de Compra Unitário (R$): "))
        margem_percentual = float(input("Insira a Margem de Lucro Desejada (em % de lucro sobre o custo, ex: 50): "))
    except ValueError:
        print("\nErro: Insira apenas números válidos.")
        input("Pressione Enter para voltar.")
        return
        
    margem_decimal = margem_percentual / 100
    
    # Preço Otimizado = Custo * (1 + Margem Desejada)
    preco_otimizado = custo * (1 + margem_decimal)
    
    print("\n--- Resultado da Otimização ---")
    print(f"Margem de Lucro Desejada: {margem_percentual:.2f}%")
    print(f"Preço de Venda Mínimo para atingir essa margem: R$ {preco_otimizado:,.2f}")
    
    input("\nPressione Enter para voltar.")


def inserir_analise_abc():
    """Opção 2.4: Análise ABC Simples (Interativo com DF Coletado)."""
    limpar_tela()
    print("--- 2.4 Análise ABC Simples (Foco em % de Faturamento) ---")
    
    try:
        percentual = float(input("Insira o percentual de faturamento para análise ABC (ex: 80 para Categoria A): "))
        if percentual <= 0 or percentual > 100:
            raise ValueError
    except ValueError:
        print("\nErro: O percentual deve ser um número entre 1 e 100.")
        input("Pressione Enter para voltar.")
        return
        
    # Agrupar por produto e calcular o faturamento total
    df_faturamento = df_vendas.groupby('Produto')['Total_Venda'].sum().reset_index()
    df_faturamento = df_faturamento.sort_values(by='Total_Venda', ascending=False)
    
    # Calcular o percentual acumulado
    total_faturamento_geral = df_faturamento['Total_Venda'].sum()
    df_faturamento['Percentual_Acumulado'] = (df_faturamento['Total_Venda'].cumsum() / total_faturamento_geral) * 100
    
    # Selecionar os produtos que atingem o percentual desejado
    produtos_abc = df_faturamento[df_faturamento['Percentual_Acumulado'] <= percentual]
    
    print(f"\n--- Produtos que representam {percentual:.0f}% do Faturamento Total ---")
    if not produtos_abc.empty:
        # Usa to_string para formatação limpa no console
        print(produtos_abc[['Produto', 'Total_Venda', 'Percentual_Acumulado']].to_string(index=False))
        print(f"\nTotal de {len(produtos_abc)} produtos são responsáveis por esta fatia do faturamento.")
    else:
        print("\nNenhum produto atinge o percentual ou o percentual é muito baixo.")
        
    input("\nPressione Enter para voltar.")


def inserir_simulacao_saida_estoque():
    """Opção 2.5: Simulação de Saída de Estoque (Interativo)."""
    limpar_tela()
    print("--- 2.5 Simulação de Saída de Estoque (Estimativa de Duração) ---")

    print("\nProdutos disponíveis na base de dados:")
    for i, prod in enumerate(lista_produtos):
        print(f"{i+1}. {prod}")
        
    try:
        escolha = int(input("Selecione o número do produto para simular a demanda: "))
        produto_simulado = lista_produtos[escolha - 1]
        estoque_atual = int(input(f"Insira a quantidade em estoque atual de '{produto_simulado}': "))
    except (ValueError, IndexError):
        print("\nErro: Seleção ou quantidade inválida.")
        input("Pressione Enter para voltar.")
        return

    # 1. Calcular a Média de Venda Diária (MVD) para o produto selecionado
    df_produto = df_vendas[df_vendas['Produto'] == produto_simulado]
    if df_produto.empty:
        print("\nErro: Produto não encontrado nos dados históricos.")
        input("Pressione Enter para voltar.")
        return
        
    # Garante que o cálculo seja baseado no período real de tempo
    dias_ativos = (df_produto['Data_Venda'].max() - df_produto['Data_Venda'].min()).days + 1
    total_vendido = df_produto['Quantidade'].sum()
    mvd = total_vendido / dias_ativos if dias_ativos > 0 else total_vendido

    print("\n--- Resultado da Simulação de Estoque ---")
    print(f"Média de Venda Diária (MVD) para '{produto_simulado}': {mvd:.2f} unidades/dia.")
    
    if mvd > 0:
        dias_para_fim = estoque_atual / mvd
        print(f"Com base na MVD, o estoque atual de {estoque_atual} unidades durará: **{dias_para_fim:.1f} dias**.")
        if dias_para_fim < 30:
             print("\n⚠️ AVISO: O estoque pode durar menos de um mês. Considere uma nova compra!")
    else:
        print("MVD zero. O produto pode não ter sido vendido ou os dados são insuficientes.")

    input("\nPressione Enter para voltar.")


# =================================================================
# 2. FLUXO PRINCIPAL (LOGIN E MENUS)
# =================================================================

def menu_dados_coletados():
    """Menu para a Opção 1: Análises Prontas (Dados Coletados)."""
    while True:
        limpar_tela()
        print("=" * 40)
        print("  MENU 1: DADOS COLETADOS (Análises Prontas)")
        print("=" * 40)
        print("1. Lucro Anual Total (com Gráfico de Tendência)")
        print("2. Lucro Médio Mensal (e Top Produtos em Lucro)")
        print("3. Lucro sobre Produto (Margem Média)")
        print("4. Previsão de Estoque (Simulação Scikit-learn)")
        print("5. Produtos Mais Lucrativos (Ranking e % de Categoria)")
        print("6. Voltar ao Menu Principal")
        print("-" * 40)
        
        escolha = input("Selecione a opção desejável (1-6): ")
        
        if escolha == '1':
            analise_lucro_anual(df_vendas)
        elif escolha == '2':
            analise_lucro_mensal(df_vendas)
        elif escolha == '3':
            analise_lucro_sobre_produto(df_vendas)
        elif escolha == '4':
            previsao_de_estoque(df_vendas)
        elif escolha == '5':
            analise_produtos_mais_lucrativos(df_vendas)
        elif escolha == '6':
            break
        else:
            print("\nOpção inválida. Tente novamente.")
            time.sleep(1)

def menu_dados_inseridos():
    """Menu para a Opção 2: Análises Interativas (Dados Inseridos)."""
    while True:
        limpar_tela()
        print("=" * 40)
        print("  MENU 2: DADOS INSERIDOS (Simulação Interativa)")
        print("=" * 40)
        print("1. Prever Demanda (Simples com Fator de Crescimento)")
        print("2. Calcular Lucro (Insira Custo, Preço e Quantidade)")
        print("3. Otimizar Preço (Defina Margem de Lucro Desejada)")
        print("4. Análise ABC Simples (Foco em % de Faturamento)")
        print("5. Simulação de Saída de Estoque (Estoque vs. MVD)")
        print("6. Voltar ao Menu Principal")
        print("-" * 40)
        
        escolha = input("Selecione a opção desejável (1-6): ")
        
        if escolha == '1':
            inserir_previsao_demanda()
        elif escolha == '2':
            inserir_calcular_lucro()
        elif escolha == '3':
            inserir_otimizar_preco()
        elif escolha == '4':
            inserir_analise_abc()
        elif escolha == '5':
            inserir_simulacao_saida_estoque()
        elif escolha == '6':
            break
        else:
            print("\nOpção inválida. Tente novamente.")
            time.sleep(1)


def menu_principal():
    """Menu Principal após o login."""
    while True:
        limpar_tela()
        print("=" * 40)
        print("  SISTEMA DE GESTÃO DE ESTOQUE (SIMULAÇÃO)")
        print("=" * 40)
        print("1. Dados Coletados (Análises Prontas)")
        print("2. Dados Inseridos (Simulação Interativa)")
        print("3. Sair")
        print("-" * 40)
        
        escolha = input("Selecione a opção desejável (1/2/3): ")
        
        if escolha == '1':
            menu_dados_coletados()
        elif escolha == '2':
            menu_dados_inseridos()
        elif escolha == '3':
            limpar_tela()
            print("Saindo do programa. Obrigado!")
            break
        else:
            print("\nOpção inválida. Tente novamente.")
            time.sleep(1)


def tela_login():
    """Tela de login com as credenciais fixas."""
    # Variáveis de Login (EXATAMENTE como pedido)
    LOGIN_CORRETO = "Admin"
    SENHA_CORRETA = "Admin123"

    max_tentativas = 3
    tentativas = 0
    
    while tentativas < max_tentativas:
        limpar_tela()
        print("=" * 40)
        print("            TELA DE LOGIN")
        print("=" * 40)
        login = input("Login: ")
        senha = input("Senha: ")
        
        if login == LOGIN_CORRETO and senha == SENHA_CORRETA:
            limpar_tela()
            print("Login bem-sucedido! Bem-vindo, Admin.")
            time.sleep(1.5)
            menu_principal()
            return
        else:
            tentativas += 1
            restantes = max_tentativas - tentativas
            if restantes > 0:
                print(f"\nCredenciais inválidas. Você tem mais {restantes} tentativa(s).")
                time.sleep(2)
            else:
                limpar_tela()
                print("Número máximo de tentativas alcançado. Fechando o programa.")
                time.sleep(2)
                return

# =================================================================
# 3. INICIALIZAÇÃO DO PROGRAMA
# =================================================================

if __name__ == "__main__":
    tela_login()