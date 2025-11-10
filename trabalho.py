import pandas as pd
import numpy as np
from datetime import timedelta, date
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression 
import time 
import io
from wordcloud import WordCloud

def salvar_grafico_para_memoria(plt_obj):
    """Salva o gráfico do Matplotlib em um buffer de memória (BytesIO)."""
    buffer = io.BytesIO()
    plt_obj.savefig(buffer, format='png')
    buffer.seek(0)
    plt_obj.close()
    return buffer

def analise_lucro_anual(df_vendas):
    lucro_total = df_vendas['Lucro_Bruto'].sum()
    
    df_mensal = df_vendas.set_index('Data_Venda')['Lucro_Bruto'].resample('ME').sum()
    
    plt.figure(figsize=(10, 6))
    df_mensal.plot(kind='line', marker='o', color='green')
    plt.title('Tendência de Lucro Mensal')
    plt.xlabel('Mês')
    plt.ylabel('Lucro Bruto (R$)')
    plt.grid(True)
    plt.tight_layout()

    mensagem = f"💰 **Análise 1.1: Lucro Anual Total**\n"
    mensagem += f"O Lucro Bruto Total acumulado é de: **R$ {lucro_total:,.2f}**."
    
    return salvar_grafico_para_memoria(plt), mensagem

def analise_lucro_mensal(df_vendas):
    df_mensal = df_vendas.set_index('Data_Venda')['Lucro_Bruto'].resample('ME').sum()
    lucro_medio_mensal = df_mensal.mean()
    
    df_lucro_produto = df_vendas.groupby('Produto')['Lucro_Bruto'].sum().sort_values(ascending=False).head(5)
    
    plt.figure(figsize=(10, 6))
    df_lucro_produto.plot(kind='bar', color='blue')
    plt.title('Top 5 Produtos por Lucro Bruto')
    plt.xlabel('Produto')
    plt.ylabel('Lucro Bruto (R$)')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    mensagem = f"📊 **Análise 1.2: Lucro Médio Mensal**\n"
    mensagem += f"Lucro Bruto Médio Mensal: **R$ {lucro_medio_mensal:,.2f}**\n\n"
    mensagem += "🏆 **Top 3 Meses:**\n"
    mensagem += df_mensal.nlargest(3).apply(lambda x: f"R$ {x:,.2f}").to_string()
    
    return salvar_grafico_para_memoria(plt), mensagem

def analise_lucro_sobre_produto(df_vendas):
    df_vendas['Margem_Lucro'] = (df_vendas['Preco_Venda'] - df_vendas['Custo_Unitario']) / df_vendas['Preco_Venda']
    margens_medias = df_vendas.groupby('Produto')['Margem_Lucro'].mean().sort_values(ascending=False)
    
    plt.figure(figsize=(10, 6))
    (margens_medias * 100).plot(kind='barh', color='darkred')
    plt.title('Margem de Lucro Média por Produto')
    plt.xlabel('Margem de Lucro Média (%)')
    plt.ylabel('Produto')
    plt.tight_layout()

    mensagem = f"📈 **Análise 1.3: Margem Média (Top 3)**\n"
    mensagem += margens_medias.head(3).apply(lambda x: f"{x * 100:.2f}%").to_string()
    
    return salvar_grafico_para_memoria(plt), mensagem

def previsao_de_estoque(df_vendas):
    df_vendas['Dia_do_Ano'] = df_vendas['Data_Venda'].dt.dayofyear
    
    produto_previsao = df_vendas['Produto'].value_counts().idxmax()
    df_prod_b = df_vendas[df_vendas['Produto'] == produto_previsao]
    
    X = df_prod_b[['Dia_do_Ano']]
    y = df_prod_b['Quantidade']
    
    model = LinearRegression()
    model.fit(X, y)
    
    dia_futuro = df_vendas['Data_Venda'].max().dayofyear + 30 
    X_futuro = pd.DataFrame({'Dia_do_Ano': [dia_futuro]})
    previsao_qty = model.predict(X_futuro)[0]
    
    df_mensal = df_vendas[df_vendas['Produto'] == produto_previsao].set_index('Data_Venda')['Quantidade'].resample('ME').sum()
    
    plt.figure(figsize=(10, 6))
    df_mensal.plot(kind='bar', color='orange')
    plt.title(f'Vendas Mensais de {produto_previsao} vs. Projeção')
    plt.xlabel('Mês')
    plt.ylabel('Quantidade Vendida')
    plt.axhline(previsao_qty * 30, color='red', linestyle='--', label=f'Projeção Mês Futuro ({previsao_qty * 30:.0f} unid.)')
    plt.legend()
    plt.tight_layout()

    mensagem = f"🔮 **Análise 1.4: Previsão de Estoque ({produto_previsao})**\n"
    mensagem += f"Previsão de Quantidade Média de Venda para o dia {dia_futuro} (futuro): **{max(1, round(previsao_qty)):.0f} unidades**."
    
    return salvar_grafico_para_memoria(plt), mensagem

def analise_produtos_mais_lucrativos(df_vendas):
    lucro_por_categoria = df_vendas.groupby('Categoria')['Lucro_Bruto'].sum().sort_values(ascending=False)
    
    plt.figure(figsize=(8, 5))
    lucro_por_categoria.plot(kind='pie', autopct='%1.1f%%', startangle=90, colors=['#ff9999','#66b3ff','#99ff99', '#ffcc99'])
    plt.title('Distribuição Percentual do Lucro Bruto por Categoria (Tipo de Pagamento)')
    plt.ylabel('')
    plt.tight_layout()
    
    produto_mais_lucrativo = df_vendas.groupby('Produto')['Lucro_Bruto'].sum().idxmax()
    lucro_max = df_vendas.groupby('Produto')['Lucro_Bruto'].sum().max()

    mensagem = f"👑 **Análise 1.5: Ranking de Lucratividade**\n"
    mensagem += f"O item mais lucrativo é: **{produto_mais_lucrativo}** (R$ {lucro_max:,.2f})\n\n"
    mensagem += "💰 **Lucro por Tipo de Pagamento:**\n"
    mensagem += lucro_por_categoria.apply(lambda x: f"R$ {x:,.2f}").to_string()
    
    return salvar_grafico_para_memoria(plt), mensagem

def analise_nuvem_lucro(df_vendas):
    df_lucro = df_vendas.groupby('Produto')['Lucro_Bruto'].sum()
    df_lucro = df_lucro[df_lucro > 0]
    
    frequencias_dict = df_lucro.to_dict()
    
    if not frequencias_dict:
        return None, "❌ Erro: Nenhum dado de produto com lucro positivo para gerar a nuvem de palavras."

    wc = WordCloud(width=800, height=400,
                   background_color='white',
                   colormap='plasma', 
                   min_font_size=10).generate_from_frequencies(frequencias_dict)
    
    plt.figure(figsize=(10, 7))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    plt.title('Nuvem de Palavras por Lucro Bruto Total')
    plt.tight_layout(pad=0)
    
    mensagem = "☁️ **Análise 1.8: Nuvem de Palavras (Lucro)**\n"
    mensagem += "Esta nuvem de palavras mostra os produtos que geraram mais lucro. Quanto maior o nome, maior o lucro total."
    
    return salvar_grafico_para_memoria(plt), mensagem



def inserir_previsao_demanda(df_vendas_global, fator_crescimento, estoque_atual):
    dias_no_ano = 365
    venda_diaria_media = df_vendas_global['Quantidade'].sum() / dias_no_ano
    
    nova_venda_diaria = venda_diaria_media * (1 + fator_crescimento / 100)
    
    dias_restantes = estoque_atual / nova_venda_diaria if nova_venda_diaria > 0 else "Indefinido (Venda 0)"
    
    mensagem = "📈 **Resultado da Simulação de Demanda**\n"
    mensagem += f"Média de Vendas Diárias (Base Histórica): {venda_diaria_media:.2f} unidades.\n"
    mensagem += f"Projeção de Nova Média Diária (com {fator_crescimento:.0f}% de Crescimento): {nova_venda_diaria:.2f} unidades.\n\n"
    mensagem += f"Se o crescimento for atingido, seu estoque atual de {estoque_atual} unidades durará: **{dias_restantes:.1f} dias**."
    return mensagem


def inserir_calcular_lucro(custo, preco_venda, quantidade):
    lucro_unitario = preco_venda - custo
    lucro_total = lucro_unitario * quantidade
    
    mensagem = "💸 **Resultado do Cálculo de Lucro**\n"
    mensagem += f"Lucro Unitário: R$ {lucro_unitario:,.2f}\n"
    mensagem += f"Lucro Total (em {quantidade} unidades): **R$ {lucro_total:,.2f}**"
    
    if preco_venda < custo:
        mensagem += "\n\n⚠️ **AVISO:** O Preço de Venda é menor que o Custo! Você terá prejuízo."
        
    return mensagem


def inserir_otimizar_preco(custo, margem_percentual):
    margem_decimal = margem_percentual / 100
    preco_otimizado = custo * (1 + margem_decimal)
    
    mensagem = "💡 **Resultado da Otimização de Preço**\n"
    mensagem += f"Margem de Lucro Desejada: {margem_percentual:.2f}%\n"
    mensagem += f"Preço de Venda Mínimo para atingir essa margem: **R$ {preco_otimizado:,.2f}**"
    return mensagem


def inserir_analise_abc(df_vendas_global, percentual):
    df_faturamento = df_vendas_global.groupby('Produto')['Total_Venda'].sum().reset_index()
    df_faturamento = df_faturamento.sort_values(by='Total_Venda', ascending=False)
    
    total_faturamento_geral = df_faturamento['Total_Venda'].sum()
    df_faturamento['Percentual_Acumulado'] = (df_faturamento['Total_Venda'].cumsum() / total_faturamento_geral) * 100
    
    produtos_abc = df_faturamento[df_faturamento['Percentual_Acumulado'] <= percentual]
    
    mensagem = f"🅰️ **Análise ABC (Produtos que somam {percentual:.0f}% do Faturamento)**\n"
    
    if not produtos_abc.empty:
        mensagem += "```\n"
        mensagem += produtos_abc[['Produto', 'Total_Venda', 'Percentual_Acumulado']].to_string(index=False)
        mensagem += "\n```"
        mensagem += f"\nTotal de **{len(produtos_abc)}** produtos são responsáveis por esta fatia do faturamento."
    else:
        mensagem += "Nenhum produto atinge o percentual ou o percentual é muito baixo."
        
    return mensagem

def inserir_simulacao_saida_estoque(df_vendas_global, produto_simulado, estoque_atual):
    df_produto = df_vendas_global[df_vendas_global['Produto'] == produto_simulado]
    if df_produto.empty:
        return f"Erro: Produto '{produto_simulado}' não encontrado nos dados históricos."
        
    dias_ativos = (df_produto['Data_Venda'].max() - df_produto['Data_Venda'].min()).days + 1
    total_vendido = df_produto['Quantidade'].sum()
    mvd = total_vendido / dias_ativos if dias_ativos > 0 else total_vendido

    mensagem = f"⏳ **Simulação de Saída de Estoque ({produto_simulado})**\n"
    mensagem += f"Média de Venda Diária (MVD) histórica: **{mvd:.2f} unidades/dia**.\n"
    
    if mvd > 0:
        dias_para_fim = estoque_atual / mvd
        mensagem += f"Com base na MVD, o estoque atual de {estoque_atual} unidades durará: **{dias_para_fim:.1f} dias**."
        if dias_para_fim < 30:
             mensagem += "\n\n⚠️ **AVISO:** O estoque pode durar menos de um mês. Considere uma nova compra!"
    else:
        mensagem += "MVD zero. O produto pode não ter sido vendido ou os dados são insuficientes."

    return mensagem

def simular_ponto_equilibrio(custo_fixo, custo_variavel_unit, preco_venda_unit):
    if preco_venda_unit <= custo_variavel_unit:
        return "❌ **Erro:** O Preço de Venda deve ser maior que o Custo Variável para haver lucro."
        
    margem_contribuicao = preco_venda_unit - custo_variavel_unit
    unidades_necessarias = custo_fixo / margem_contribuicao
    
    faturamento_necessario = unidades_necessarias * preco_venda_unit
    
    mensagem = f"⚖️ **Análise de Ponto de Equilíbrio**\n\n"
    mensagem += f"Com Custos Fixos de **R$ {custo_fixo:,.2f}** e uma Margem de Contribuição de **R$ {margem_contribuicao:,.2f}** por produto:\n\n"
    mensagem += f"Você precisa vender **{unidades_necessarias:.0f} unidades** para atingir o ponto de equilíbrio (não ter lucro nem prejuízo).\n"
    mensagem += f"Isso representa um faturamento total de **R$ {faturamento_necessario:,.2f}**."
    return mensagem

def simular_comparar_produtos(nome_a, custo_a, nome_b, custo_b, preco_venda_comum):
    lucro_a = preco_venda_comum - custo_a
    lucro_b = preco_venda_comum - custo_b
    
    margem_a_percent = (lucro_a / preco_venda_comum) * 100
    margem_b_percent = (lucro_b / preco_venda_comum) * 100
    
    mensagem = f"🆚 **Comparação de Lucratividade (Preço de Venda: R$ {preco_venda_comum:,.2f})**\n\n"
    mensagem += f"**Produto A ({nome_a}):**\n"
    mensagem += f"   - Custo: R$ {custo_a:,.2f}\n"
    mensagem += f"   - Lucro por Venda: **R$ {lucro_a:,.2f}**\n"
    mensagem += f"   - Margem de Lucro: **{margem_a_percent:.1f}%**\n\n"
    
    mensagem += f"**Produto B ({nome_b}):**\n"
    mensagem += f"   - Custo: R$ {custo_b:,.2f}\n"
    mensagem += f"   - Lucro por Venda: **R$ {lucro_b:,.2f}**\n"
    mensagem += f"   - Margem de Lucro: **{margem_b_percent:.1f}%**\n\n"
    
    if lucro_a > lucro_b:
        mensagem += f"🏆 **Conclusão:** O **Produto A ({nome_a})** é **R$ {lucro_a - lucro_b:,.2f}** mais lucrativo por venda."
    elif lucro_b > lucro_a:
        mensagem += f"🏆 **Conclusão:** O **Produto B ({nome_b})** é **R$ {lucro_b - lucro_a:,.2f}** mais lucrativo por venda."
    else:
        mensagem += "⚖️ **Conclusão:** Ambos os produtos têm a mesma lucratividade."
        
    return mensagem