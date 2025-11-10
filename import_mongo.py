import pandas as pd
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import sys

print("Iniciando script de importação para o MongoDB...")

load_dotenv()
MONGO_URI = os.getenv('MONGO_URI')

if not MONGO_URI:
    print("ERRO: MONGO_URI não encontrada no .env. Verifique seu arquivo.")
    sys.exit(1) 

try:
    client = MongoClient(MONGO_URI)
    client.admin.command('ping')
    print("Conexão com MongoDB Atlas estabelecida com sucesso!")
except Exception as e:
    print(f"ERRO: Não foi possível conectar ao MongoDB. Verifique sua MONGO_URI e o acesso de rede.")
    print(f"Detalhe do erro: {e}")
    sys.exit(1)


db = client['empresa_ti']
collection_vendas = db['vendas']
collection_usuarios = db['usuarios'] 

caminho_csv = os.path.join('data', 'database_TI.csv')
try:
    df = pd.read_csv(caminho_csv)
    print(f"Arquivo '{caminho_csv}' carregado. {len(df)} linhas encontradas.")
except FileNotFoundError:
    print(f"ERRO: Arquivo '{caminho_csv}' não encontrado.")
    sys.exit(1)


df['DATE'] = pd.to_datetime(df['DATE'])
df['DATETIME'] = pd.to_datetime(df['DATETIME'])


data_dict = df.to_dict('records')


try:
    print("\nLimpando dados antigos da coleção 'vendas'...")
    collection_vendas.delete_many({})
    print("Dados antigos removidos.")

    print(f"Inserindo {len(data_dict)} novos documentos na coleção 'vendas'...")
    collection_vendas.insert_many(data_dict)
    
    if collection_usuarios.count_documents({}) == 0:
        collection_usuarios.create_index('user_id', unique=True)
        print("Coleção 'usuarios' inicializada com índice único.")

    print(f"\n✅ SUCESSO! Dados importados para o MongoDB.")

except Exception as e:
    print(f"ERRO: Falha ao inserir dados no MongoDB.")
    print(f"Detalhe do erro: {e}")

client.close()
print("Conexão com MongoDB fechada.")