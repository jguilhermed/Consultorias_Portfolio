import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import warnings
from PIL import Image
import altair 
import matplotlib.pyplot as plt

#Desetivando warnings de descontinuação de pacotes:
st.set_option('deprecation.showPyplotGlobalUse', False)


#Funções:

#1 - Carregamento dos dados

def carrega_dados(x):
    
    dados = pd.read_excel(x)
    return dados

#2 - Tratamento dos Dados
def organiza_dados(dados):
    
    #Definindo colunas úteis
    colunas = ['Cadastro', 'Serviços', 'Nascimento', 
               'Gênero', 'Endereço', 'Bairro', 'CEP', 'Estado res.', 'Cidade res.']
    
    #Aplicando colunas úteis
    dados = dados[colunas]
    
    #Renomear Colunas
    dados = dados.rename(columns = {'Estado res.': 'Estado',
                                   'Cidade res.': 'Cidade',
                                   'Gênero': 'Genero', 
                                   'Serviços': 'Servico',
                                   'Endereço': 'Endereco'}) 
    
    dados.dropna(inplace = True)
    
    #Datetime
    dados['Cadastro'] = pd.to_datetime(dados['Cadastro'], dayfirst=True )
    dados['Ano'] = dados['Cadastro'].dt.year
    dados['Mes'] = dados['Cadastro'].dt.month
    
    #Calculando Idade
    dados['Nascimento'] = pd.to_datetime(dados['Nascimento'], dayfirst=True) 
    dados['Idade'] = dados['Ano'] - dados['Nascimento'].dt.year   
    
    #imputando idades discrepantes
    idade_imput = dados['Idade'].median()
    dados['Idade'].replace(0,idade_imput, inplace=True) 
    
    #Generalização serviços
    dados['Servico'].replace(to_replace = ['RENOVAÇÃO 1ª HABILITAÇÃO B',  'ADIÇÃO A',
                                           'CNH DEFINITIVA', 
                                           'RENOVAÇÃO C/ TRANSF. DE PRONT.', 'RENOVAÇÃO', 
                                           'CURSO DE ATUALIZAÇÃO', 
                                           '1ª HABILITAÇÃO AB 1ª HABILITAÇÃO B', 'ALTERAÇÃO DE DADOS (EAR)',
                                           'ADIÇÃO CAT. B', 'PARTE PRATICA A 1ª HABILITAÇÃO A',
                                           'REABILITAÇÃO', 'PARTE PRATICA AB', 'PARTE PRATICA B',
                                           'ALTERAÇÃO DE DADOS (EAR) 1ª HABILITAÇÃO AB', 'AULA AVULSA B',
                                           'RENOVAÇÃO C/ TRANSF. DE PRONT. RENOVAÇÃO',
                                           '1ª HABILITAÇÃO B 1ª HABILITAÇÃO AB',
                                           'PARTE PRATICA AB 1ª HABILITAÇÃO AB',
                                           'RENOVAÇÃO 1ª HABILITAÇÃO AB', '2ª VIA CNH',
                                           '1ª HABILITAÇÃO AB 1ª HABILITAÇÃO A',
                                           'TRANSFERENCIA DE PRONTUARIO'], 
                            value = 'OUTROS', inplace = True)
    
    
    #Extraindo nome da rua
    dados['Rua'] = dados['Endereco'].apply(lambda x : x.split('.')[1])
    
    #Excluindo colunas e reorganizando índices
    dados.drop(columns = ['Cadastro', 'Nascimento', 'Endereco'], inplace = True)
    dados = dados.reset_index()
    dados.drop(columns = 'index', inplace = True)
    
    return dados

#Versões dos dados com filtros específicos

def v2_dados(dados):

    dados_2 = dados.groupby(['Mes', 'Servico', 'Ano', 'Genero', 'Idade'], as_index = False).agg({'Bairro': 'count'})
    dados_2['Faixa_Etaria'] = pd.cut(dados_2['Idade'], 4, labels = ['18-23', '24-29', '30-35', '>35'] )
    dados_2.rename(columns = {'Bairro': 'Qtd'}, inplace = True)
    return dados_2

def ABm(dados_2):

    AB_B_A_mensal = dados_2[(dados_2.Servico == '1ª HABILITAÇÃO AB') | (dados_2.Servico == '1ª HABILITAÇÃO B') | (dados_2.Servico == '1ª HABILITAÇÃO A')].groupby('Mes', as_index = False).agg({'Qtd': 'sum'})
    AB_mensal = dados_2[dados_2.Servico == '1ª HABILITAÇÃO AB'].groupby('Mes', as_index = False).agg({'Qtd': 'sum'})
    B_mensal = dados_2[dados_2.Servico == '1ª HABILITAÇÃO B'].groupby('Mes', as_index = False).agg({'Qtd': 'sum'})
    return AB_B_A_mensal, AB_mensal, B_mensal

def principal():
    #Exibe logo Harmonia
    logo = Image.open('Logo_Harmonia.jpeg')
    st.image(logo, caption=None, width=None, use_column_width=None, clamp=False, channels="RGB", output_format="auto")

    #Título 
    st.title("Dashboard Analítico - CFC Harmonia")

    #Upload da planilha de dados
    #dados_brutos = st.file_uploader("Buscar Planilha", type=['xlsx', 'csv'])
    dados_brutos = carrega_dados('Listagem_Harmonia_Detran-net-Sig.xlsx')

    #Aplica tratamento nos dados e cria as versões dos datasets utilizados
    dados = organiza_dados(dados=dados_brutos)
    dados2 = v2_dados(dados=dados)
    AB_B_A_mensal, AB_mensal, B_mensal = ABm(dados2)
    
   
    #Visualização da Tabela 
    st.header("Visualização da Tabela Principal:")
    st.dataframe(data=dados, use_container_width=True)

    #Gráfico de Barras - Serviços ao longo do ano.
    st.header("Serviços Realizados Mensalmente Por Tipo:")
    chart = altair.Chart(dados2).mark_bar(size=30).encode(
        x='Mes',
        y='Qtd',
        color='Servico').interactive()
    st.altair_chart(chart, theme="streamlit", use_container_width=True)

    # Funil Serviços
    st.header('Percentual de Serviços Prestados:')
    funil_serv = px.funnel_area(data_frame=dados2, names='Servico')
    st.plotly_chart(funil_serv)

    #Gráfico de Barras da Categoria AB_A_mensal
    st.header("Habilitações Categoria AB, B e A Realizadas Mensalmente")
    chart = altair.Chart(AB_B_A_mensal).mark_bar(size=70).encode(
        x='Mes',
        y='Qtd').interactive()
    st.altair_chart(chart, theme="streamlit", use_container_width=True)

    #Gráfico de Barras da Categoria B_mensal
    st.header("Habilitações Categoria B Realizadas Mensalmente")
    chart = altair.Chart(B_mensal).mark_bar(size=70).encode(
        x='Mes',
        y='Qtd').interactive()
    st.altair_chart(chart, theme="streamlit", use_container_width=True)

    #Gráfico de Barras da Categoria AB_mensal
    st.header("Habilitações Categoria AB Realizadas Mensalmente")
    chart = altair.Chart(AB_mensal).mark_bar(size=70).encode(
        x='Mes',
        y='Qtd').interactive()
    st.altair_chart(chart, theme="streamlit", use_container_width=True)

         #Gráfico de Barras - Serviços por faixa Etária.
    st.header("Serviços Realizados Por Faixa Etária:")
    chart = altair.Chart(dados2).mark_bar(size=70).encode(
        x='Servico',
        y='Qtd',
        color='Faixa_Etaria').interactive()
    st.altair_chart(chart, theme='streamlit', use_container_width=True)

         #Gráfico de Barras - Serviços por Gênero.
    st.header("Serviços Realizados Por Genero:")
    chart = altair.Chart(dados2).mark_bar(size=70).encode(
        x='Servico',
        y='Qtd',
        color='Genero').interactive()
    st.altair_chart(chart, theme='streamlit', use_container_width=True)

    #Distribuição dos Bairros
    st.header("Percentual de Presença nos Bairros de São José:")
    funil_bairros = px.funnel_area(data_frame=dados, names='Bairro')
    st.plotly_chart(funil_bairros)

    #Modelo de Regressão Quadrática
    x = AB_B_A_mensal['Mes'].values
    y = AB_B_A_mensal['Qtd'].values
    xx = np.linspace(1,12,12)
    yy = np.poly1d(np.polyfit(x,y,2))
    y0 = yy(xx)
    y1 = []
    for i in y0:
        y1.append(round(i))

    y2 = []
    for i in y1:
        y2.append(round(i*1.25))

    y3 = []
    for i in y:
        y3.append(i)
    while len(y3)<len(y2):
        y3.append(0)

    pred = pd.DataFrame({'Previsto': y1,
                         'Meta_Mensal': y2,
                         'Realizado': y3}, index=list(range(1,13)))
    st.header("Previsão e Metas Para Matrículas de 1ª Habilitação Para os Próximos Meses:")
    st.dataframe(pred)

    st.header("Gráfico das Previsões e Metas Para os Próximos Meses:")
    st.line_chart(pred)

if __name__== '__main__':
    principal()

