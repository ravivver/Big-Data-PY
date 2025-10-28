import pandas as pd
import numpy as np
from datetime import timedelta, date
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression 
import time 

# =================================================================
# 0. CARREGAMENTO E TRATAMENTO DOS DADOS REAIS (DADOS COLETADOS)
# =================================================================

# 1. Carregamento do CSV
try:
    # O arquivo está na subpasta 'data/'.
    df_vendas = pd.read_csv('data/database.csv')
except FileNotFoundError:
    print("ERRO: Arquivo 'database.csv' não encontrado. Certifique-se de que está na pasta 'data/' dentro do diretório do script.")
    exit()

# === PASSO CRÍTICO: LIMPEZA DE COLUNAS ===
# Remove espaços em branco (leading/trailing) e padroniza para MAIÚSCULAS
df_vendas.columns = df_vendas.columns.str.strip().str.upper()
# ==========================================

# 2. Tratamento de Datas (Garante o tipo datetime)
# Convertemos a coluna original 'DATETIME' para o tipo datetime.
df_vendas['DATETIME'] = pd.to_datetime(df_vendas['DATETIME'])

# 3. Renomear colunas para o padrão do projeto
df_vendas.rename(columns={
    'DATETIME': 'Data_Venda',
    'MONEY': 'Preco_Venda',
    'COFFEE_NAME': 'Produto'
}, inplace=True)

# 4. Garante que a data seja o índice para futuras análises (resample)
df_vendas.set_index('Data_Venda', inplace=True)

# 5. Geração de Métricas Necessárias para o Projeto (Custo, Lucro, Quantidade)
df_vendas['Quantidade'] = 1 
N_TRANSACOES = len(df_vendas)

# 6. Simulação de Custo e Categoria 
# Simulação: Custo Unitário é 40% do Preço de Venda
df_vendas['Custo_Unitario'] = df_vendas['Preco_Venda'] * 0.40

# Usaremos o CASH_TYPE como 'Categoria' para as análises de agrupamento
df_vendas['Categoria'] = df_vendas['CASH_TYPE']

# 7. Cálculo Final das Métricas (Dados "Tratados" e prontos para uso)
df_vendas['Total_Venda'] = df_vendas['Preco_Venda'] * df_vendas['Quantidade']
df_vendas['Custo_Total'] = df_vendas['Custo_Unitario'] * df_vendas['Quantidade']
df_vendas['Lucro_Bruto'] = df_vendas['Total_Venda'] - df_vendas['Custo_Total']

# Lista de produtos únicos para o Menu 2
lista_produtos = df_vendas['Produto'].unique().tolist()


# =================================================================
# 1. FUNÇÕES DE EXIBIÇÃO E CÁLCULO
# O restante do código permanece inalterado, pois as funções
# de análise e menu já estão corretas.
# =================================================================

def limpar_tela():
    print("\n" * 50) 

def exibir_grafico(df, titulo="Gráfico de Análise", x_label="Eixo X", y_label="Eixo Y"):
    print(f"\n--- {titulo} ---")
    
    try:
        plt.show() 
    except Exception as e:
        print(f"[Simulação de Gráfico: Plote real será exibido em um ambiente adequado (IDE/Jupyter). Erro: {e}]")
        
    print(f"\n[Fim da Análise de {titulo}. Pressione Enter para voltar ao menu.]")
    input()

def analise_lucro_anual(df):
    limpar_tela()
    
    lucro_total = df['Lucro_Bruto'].sum()
    
    print("--- 1.1 Lucro Anual Total ---")
    print(f"\nO Lucro Bruto Total acumulado é de: R$ {lucro_total:,.2f}")
    
    df_mensal = df['Lucro_Bruto'].resample('ME').sum()
    
    plt.figure(figsize=(10, 6))
    df_mensal.plot(kind='line', marker='o', color='green')
    plt.title('Tendência de Lucro Mensal (Gráfico)')
    plt.xlabel('Mês')
    plt.ylabel('Lucro Bruto (R$)')
    plt.grid(True)
    plt.tight_layout()
    exibir_grafico(plt, "Lucro Anual Total")


def analise_lucro_mensal(df):
    limpar_tela()
    print("--- 1.2 Lucro Médio Mensal ---")
    
    df_mensal = df['Lucro_Bruto'].resample('ME').sum()
    lucro_medio_mensal = df_mensal.mean()
    
    print(f"\nLucro Bruto Médio Mensal: R$ {lucro_medio_mensal:,.2f}")
    print("\nOs meses com melhor desempenho foram:")
    print(df_mensal.nlargest(3).apply(lambda x: f"R$ {x:,.2f}").to_string())
    
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
    limpar_tela()
    print("--- 1.3 Lucro sobre Produto (Margem Média) ---")
    
    df['Margem_Lucro'] = (df['Preco_Venda'] - df['Custo_Unitario']) / df['Preco_Venda']
    
    margens_medias = df.groupby('Produto')['Margem_Lucro'].mean().sort_values(ascending=False)
    
    print("\nMargem de Lucro Média por Produto:")
    print(margens_medias.apply(lambda x: f"{x * 100:.2f}%").to_string())
    
    plt.figure(figsize=(10, 6))
    (margens_medias * 100).plot(kind='barh', color='darkred')
    plt.title('Margem de Lucro Média por Produto (Gráfico)')
    plt.xlabel('Margem de Lucro Média (%)')
    plt.ylabel('Produto')
    plt.tight_layout()
    exibir_grafico(plt, "Lucro sobre Produto")


def previsao_de_estoque(df):
    limpar_tela()
    print("--- 1.4 Previsão de Estoque (Demanda do Próximo Mês) ---")
    
    df['Dia_do_Ano'] = df.index.dayofyear
    
    produto_previsao = df['Produto'].value_counts().idxmax()
    df_prod_b = df[df['Produto'] == produto_previsao]
    
    X = df_prod_b[['Dia_do_Ano']]
    y = df_prod_b['Quantidade']
    
    model = LinearRegression()
    model.fit(X, y)
    
    dia_futuro = df.index.max().dayofyear + 30 
    X_futuro = pd.DataFrame({'Dia_do_Ano': [dia_futuro]})
    previsao_qty = model.predict(X_futuro)[0]
    
    print(f"\nBaseado no histórico do '{produto_previsao}':")
    print(f"Previsão de Quantidade Média de Venda para o dia {dia_futuro} (futuro): {max(1, round(previsao_qty)):.0f} unidades.")
    
    df_mensal = df_prod_b['Quantidade'].resample('ME').sum()
    
    plt.figure(figsize=(10, 6))
    df_mensal.plot(kind='bar', color='orange')
    plt.title(f'Vendas Mensais de {produto_previsao} vs. Projeção (Gráfico)')
    plt.xlabel('Mês')
    plt.ylabel('Quantidade Vendida')
    plt.axhline(previsao_qty * 30, color='red', linestyle='--', label=f'Projeção Mês Futuro ({previsao_qty * 30:.0f} unid.)')
    plt.legend()
    plt.tight_layout()
    exibir_grafico(plt, "Previsão de Estoque")


def analise_produtos_mais_lucrativos(df):
    limpar_tela()
    print("--- 1.5 Ranking de Lucratividade por Categoria ---")

    lucro_por_categoria = df.groupby('Categoria')['Lucro_Bruto'].sum().sort_values(ascending=False)
    
    print("\nLucro Bruto Total por Categoria (Tipo de Pagamento):")
    print(lucro_por_categoria.apply(lambda x: f"R$ {x:,.2f}").to_string())
    
    produto_mais_lucrativo = df.groupby('Produto')['Lucro_Bruto'].sum().idxmax()
    lucro_max = df.groupby('Produto')['Lucro_Bruto'].sum().max()
    print(f"\nO item que mais gerou lucro total é: {produto_mais_lucrativo} (R$ {lucro_max:,.2f})")

    plt.figure(figsize=(8, 5))
    lucro_por_categoria.plot(kind='pie', autopct='%1.1f%%', startangle=90, colors=['#ff9999','#66b3ff','#99ff99', '#ffcc99'])
    plt.title('Distribuição Percentual do Lucro Bruto por Categoria (Tipo de Pagamento)')
    plt.ylabel('')
    plt.tight_layout()
    exibir_grafico(plt, "Produtos Mais Lucrativos")


# -----------------------------------------------------------------
# 1.2 Funções para o Menu 2: Dados Inseridos (Interativo)
# -----------------------------------------------------------------

def inserir_previsao_demanda():
    limpar_tela()
    print("--- 2.1 Previsão de Demanda (Simples) ---")
    
    try:
        fator_crescimento = float(input("Insira o Fator de Crescimento da Demanda (%) para o próximo mês (ex: 10 para 10%): "))
        estoque_atual = int(input("Insira a Quantidade Atual em Estoque: "))
    except ValueError:
        print("\nErro: Insira apenas números válidos.")
        input("Pressione Enter para voltar.")
        return
    
    dias_no_ano = 365
    venda_diaria_media = df_vendas['Quantidade'].sum() / dias_no_ano
    
    nova_venda_diaria = venda_diaria_media * (1 + fator_crescimento / 100)
    
    print("\n--- Resultado da Simulação ---")
    print(f"Média de Vendas Diárias (Base Histórica): {venda_diaria_media:.2f} unidades.")
    print(f"Projeção de Nova Média Diária (com {fator_crescimento:.0f}% de Crescimento): {nova_venda_diaria:.2f} unidades.")
    
    dias_restantes = estoque_atual / nova_venda_diaria if nova_venda_diaria > 0 else "Indefinido (Venda 0)"
    
    print(f"Se o crescimento for atingido, seu estoque atual de {estoque_atual} unidades durará: {dias_restantes:.1f} dias.")
    
    input("\nPressione Enter para voltar.")


def inserir_calcular_lucro():
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
    
    preco_otimizado = custo * (1 + margem_decimal)
    
    print("\n--- Resultado da Otimização ---")
    print(f"Margem de Lucro Desejada: {margem_percentual:.2f}%")
    print(f"Preço de Venda Mínimo para atingir essa margem: R$ {preco_otimizado:,.2f}")
    
    input("\nPressione Enter para voltar.")


def inserir_analise_abc():
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
        
    df_faturamento = df_vendas.groupby('Produto')['Total_Venda'].sum().reset_index()
    df_faturamento = df_faturamento.sort_values(by='Total_Venda', ascending=False)
    
    total_faturamento_geral = df_faturamento['Total_Venda'].sum()
    df_faturamento['Percentual_Acumulado'] = (df_faturamento['Total_Venda'].cumsum() / total_faturamento_geral) * 100
    
    produtos_abc = df_faturamento[df_faturamento['Percentual_Acumulado'] <= percentual]
    
    print(f"\n--- Produtos que representam {percentual:.0f}% do Faturamento Total ---")
    if not produtos_abc.empty:
        print(produtos_abc[['Produto', 'Total_Venda', 'Percentual_Acumulado']].to_string(index=False))
        print(f"\nTotal de {len(produtos_abc)} produtos são responsáveis por esta fatia do faturamento.")
    else:
        print("\nNenhum produto atinge o percentual ou o percentual é muito baixo.")
        
    input("\nPressione Enter para voltar.")


def inserir_simulacao_saida_estoque():
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

    df_produto = df_vendas[df_vendas['Produto'] == produto_simulado]
    if df_produto.empty:
        print("\nErro: Produto não encontrado nos dados históricos.")
        input("Pressione Enter para voltar.")
        return
        
    dias_ativos = (df_produto.index.max() - df_produto.index.min()).days + 1
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

if __name__ == "__main__":
    tela_login()