import pandas as pd
import numpy as np
import os

print("Iniciando a modificação do CSV (v2: Renomeando para PRODUCTS)...")

# 1. Definição dos novos produtos e seus preços
novos_produtos_e_precos = {
    # Serviços
    'Serviço de Limpeza': 120.00,
    'Serviço de Formatação': 150.00,
    'Serviço de Montagem': 250.00,
    
    # Memórias (Entrada, Mediana, High-end)
    'RAM 8GB DDR4': 180.00,
    'RAM 16GB DDR4': 300.00,
    'RAM 32GB DDR5': 750.00,
    
    # Processadores (Entrada, Mediana, High-end)
    'CPU i3-12100': 600.00,
    'CPU i5-14600K': 1800.00,
    'CPU i9-14900K': 3500.00,
    
    # Placas de Vídeo (Entrada, Mediana, High-end)
    'GPU RTX 3050': 1300.00,
    'GPU RTX 4060': 2200.00,
    'GPU RTX 4080': 7000.00,
}

# Lista dos nomes dos 12 novos produtos
lista_novos_produtos = list(novos_produtos_e_precos.keys())

# 2. Carregar o CSV original
caminho_original = os.path.join('data', 'database.csv')
caminho_novo = os.path.join('data', 'database_TI.csv')

try:
    df = pd.read_csv(caminho_original)
except FileNotFoundError:
    print(f"Erro: Arquivo '{caminho_original}' não encontrado.")
    exit()

# 3. Padronizar colunas (importante)
# Remove espaços em branco e padroniza para MAIÚSCULAS
df.columns = df.columns.str.strip().str.upper()

# 4. Mapear os produtos antigos para os novos
# (Assumindo que a coluna original é 'COFFEE_NAME' após a padronização)
try:
    nomes_antigos_cafes = df['COFFEE_NAME'].unique()
except KeyError:
    print("Erro: A coluna 'COFFEE_NAME' não foi encontrada no CSV original.")
    print(f"Colunas encontradas: {df.columns.to_list()}")
    exit()
    
num_antigos = len(nomes_antigos_cafes)
num_novos = len(lista_novos_produtos)

# Criar um dicionário de mapeamento
mapa_produtos = {}
for i, nome_antigo in enumerate(nomes_antigos_cafes):
    mapa_produtos[nome_antigo] = lista_novos_produtos[i % num_novos]

print("Mapeamento criado.")

# 5. Aplicar as transformações
# Substitui os nomes na coluna 'COFFEE_NAME'
df['COFFEE_NAME'] = df['COFFEE_NAME'].map(mapa_produtos)

# Substitui os preços (MONEY) pelos novos preços
df['MONEY'] = df['COFFEE_NAME'].map(novos_produtos_e_precos)

# Adicionar uma pequena variação aleatória no preço para simular descontos
variacao = np.random.uniform(0.95, 1.05, size=len(df))
df['MONEY'] = (df['MONEY'] * variacao).round(2)

# 6. *** ALTERAÇÃO SOLICITADA ***
# Renomear a coluna de 'COFFEE_NAME' para 'PRODUCTS'
df.rename(columns={'COFFEE_NAME': 'PRODUCTS'}, inplace=True)
print("\nColuna 'COFFEE_NAME' renomeada para 'PRODUCTS'.")

# 7. Salvar o novo CSV
df.to_csv(caminho_novo, index=False)

print(f"\nSucesso! O novo arquivo com tema de TI foi salvo como '{caminho_novo}'.")
print("\nPrimeiras 5 linhas dos novos dados (com a coluna PRODUCTS):")
print(df.head())