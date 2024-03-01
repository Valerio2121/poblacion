#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import dash
# import dash_table
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd, numpy as np
import plotly.graph_objects as pg
import plotly.express as px
import plotly.io as pio
import unicodedata as ud
pio.renderers.default='png'
pd.set_option('display.max_columns', 10)
pd.set_option('display.max_rows', 10)
pd.set_option('display.width', 100)
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
import time
from urllib.parse import unquote

# funciones
def f_mark(value):
    return lista_edades2[value]


# data
df = pd.read_csv('data/pobl.csv')
df = df.rename(columns={'Country':'страна', 'Sex':'пол', 'AGE':'возраст', 'Time':'год', 'Value':'численность'})
df = df[['страна', 'пол', 'возраст', 'год', 'численность']]

paises = list(df['страна'].unique()[:-4])
paises.remove("China (People's Republic of)")
paises.append('China')
paises.sort()

df.loc[df['страна']=="China (People's Republic of)", 'страна'] = 'China'
df.loc[df['пол']=='Women', 'пол'] = 'женский'
df.loc[df['пол']=='Men', 'пол'] = 'мужской'
lista_edades = ['0_4', '05_9', '10_14', '15_19', '20_24', '25_29', '30_34', '35_39',
 '40_44', '45_49', '50_54', '55_59', '60_64', '65_69', '70_74', '75_79', '80_84', '85_OVER']
lista_edades2 = ['00_4', '05_9', '10_14', '15_19', '20_24', '25_29', '30_34', '35_39',
 '40_44', '45_49', '50_54', '55_59', '60_64', '65_69', '70_74', '75_79', '80_84', '>=85']


df2 = df[df['возраст'].isin(lista_edades)]

df2.loc[df2['возраст']=='85_OVER', 'возраст'] = '>=85'
df2.loc[df2['возраст']=='0_4', 'возраст'] = '00_4'
# df2.loc[(df2['возраст']=='00_4') & (df2['пол']=='мужской'), 'численность'] = df2['численность'] - 200000
# df2['численность по группе'] = df2[df2['пол']=='женский']['численность'] + df2[df2['пол']=='мужской']['численность']

df3 = df2[df2['пол'].isin(['мужской', 'женский'])].groupby(by=['страна', 'возраст', 'год'], as_index=False).sum()
df3.rename(columns={'численность':'численность в группе'}, inplace=True)
df2 = df2.merge(df3, how='left', on=['страна', 'возраст', 'год'])
df2['% в группе'] = np.nan
#df2.loc[df2['пол'].isin(['мужской', 'женский']), '% в группе'] = round(df2['численность']/df2['численность в группе']*100, 1)
df2.loc[df2['пол']=='женский', 'численность'] = -1*df2['численность']
#df2.loc[df2['пол']=='женский', '% в группе'] = -1*df2['% в группе']

df3 = df2[df2['пол'].isin(['мужской', 'женский'])].groupby(by=['страна', 'возраст', 'год'], as_index=False).sum()[['страна', 'возраст', 'год', 'численность']]
df3.rename(columns={'численность':'перекос'}, inplace=True)
df2 = df2.merge(df3, how='left', on=['страна', 'возраст', 'год'])
df2['цвет'] = 'женский'
df2.loc[df2['перекос']>0, 'цвет'] = 'мужской'
df2 = df2.sort_values(by=['возраст'])


# aplicacion
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

# maquetas
maqueta0 = html.Div([
    dbc.NavbarSimple([
        dbc.DropdownMenu([
            dbc.DropdownMenuItem(pais, href=pais) for pais in paises
            ], label='Выберите страну')
        ], brand='Главная', brand_href='/'),
    dcc.Markdown('''
                 ##
                 ##### Небольшое приложение, которое у вас перед глазами, позволит вам исследовать некоторые показатели, относящиеся к демографии ряда стран мира, а именно:
                     * динамику численности населения по годам;
                     * соотношение людей по возрастным группам в стране;
                     * гендерное соотношение.
                ## 
                ##### Для работы с приложением используйте всего две навигационные кнопки:
                    * **Главная** - она вас перебросит на эту страницу;
                    * **Выберите страну** - она перебросит на страницу с описанной выше информацией по выбранной стране,
                    где можно будет сравнить ее показатели с любой другой страной из списка.
                 '''),
    html.P(),
    dbc.Row([
    html.Img(src='/assets/poblacion.jpg', height=485)
    ], align='center')
    ]) 

# maqueta1 = html.Div([
#     dbc.NavbarSimple(brand='Главная', brand_href='/')
    
#     ])
                 
maqueta_general = html.Div([
    dcc.Location(id='loc_general'),
    html.Div(id='local')
    ], id='general')     

       

@app.callback(Output('local', 'children'), Input('loc_general', 'pathname'))
def mostrar_href(pathname):
    global pais_elegido
    pais_elegido = unquote(pathname[1:])
    if pais_elegido=='':
        return maqueta0
    else:
        paises1 = list(paises)
        paises1.remove(pais_elegido)
        
        return html.Div([
            dbc.NavbarSimple(pais_elegido, brand='Главная', brand_href='/',
                             style={'font-size': "25px", 'color':'#00FFFF', 'font-weight': 'bold'}),
            dbc.Row([
                dbc.Col([
                    dcc.Dropdown(id='lista_paises', options=[
                        {'label':i, 'value':i} for i in paises1], multi=True,
                        placeholder='Страны для сравнения', style={'color':'#000000', 'border-color': '#B0C4DE', })
                    ], width=5),
                dbc.Col([
                    dbc.Label('Год (анализ по половому признаку)', lg={'offset':3}),
                    dcc.Slider(id = 'slider1', min=df['год'].min(), max=df['год'].max(), 
                               included=False, dots=True, step=1, value=df['год'].max(),
                               marks={int(ano):str(ano) for ano in sorted(df['год'].unique())[::2]},
                               tooltip={"placement": "bottom", "always_visible": True})
                    ], width=7)
                ]),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='fig1_poblacion')
                    ], width=5),
                dbc.Col([
                    dcc.Graph(id='fig2_gender')
                    ], width=5),
                dbc.Col([
                    dcc.Graph(id='fig3_gender')
                    ], width=2)
                ]),
            dbc.Row([
                dbc.Col([
                    html.P(),
                    dbc.Card([
                        dbc.CardImg(
                            src="/assets/zem700.jpg",
                            top=True,
                            style={"opacity": 0.3}),
                        dbc.CardImgOverlay(
                        
                        dbc.CardBody([
                            html.H3('Страна '+pais_elegido, style={'text-align':'center'}),
                            html.P('(фильтры Год и Возраст влияют на информацию ниже)', style={'text-align':'center', 'font-size':16, 'color':'#CD5C5C'}),
                            html.P('из '+str(len(paises))+' стран в базе данных', style={'text-align':'center', 'font-size':18}),
                            html.P(id='info0', style={'text-align':'left', 'font-size':24, 'color':'#FFD700'}),
                            html.P(id='info1', style={'text-align':'left', 'font-size':18, 'color':'#00FFFF'}),
                            html.P(id='info2', style={'text-align':'left', 'font-size':18, 'color':'#FF69B4'})
                                      
                            ])
                        )
                        ])
                    ], width=5),
                dbc.Col([
                    dbc.Label('Возраст', style={'fontSize': 14, 'verticalAlign': 'bottom', 'margin-top':5}),
                    dcc.RangeSlider(id='slider2',
                                    min=0, max=len(lista_edades2)-1, step=1,
                                    marks={i:{'label':lista_edades2[i], 'style':{'fontSize':13}} for i in range(len(lista_edades2))},
                                    vertical=True, dots=False, verticalHeight=300,
                                    value=[0, len(lista_edades2)]
                                    )
                    
                    ], width={'offset':0}),
                dbc.Col([
                    html.P(),
                    dcc.Graph(id='din_gender')
                    ], width=6)
                
                ])

            ])



@app.callback(Output('info0', 'children'),
              Output('info1', 'children'),
              Output('info2', 'children'),
              Input('slider1', 'value'),
              Input('slider2', 'value'))
def f_carta(ano, grupos):
    lista_edades3 = lista_edades2[grupos[0]:grupos[1]+1]
    dfi = df2[(df2['страна'].isin(paises)) & (df2['год']==ano) & (df2['возраст'].isin(lista_edades3)) &(df2['пол'].isin(['мужской', 'женский']))]
    dfi = dfi[['страна', 'пол', 'численность']].groupby(by=['страна', 'пол'], as_index=False).sum()
    dfi.loc[dfi['пол']=='женский', 'численность'] = -1*dfi['численность']
    
    dfii = dfi[dfi['пол']=='мужской']
    dfii.sort_values(by=['численность'], ascending=False, inplace=True)
    hombres = dfii['страна'].to_list()
    lugar_hombres = hombres.index(pais_elegido)+1, round(dfii[dfii['страна']==pais_elegido]['численность'].iat[0]*10**(-6), 1)
    
    dfii = dfi[dfi['пол']=='женский']
    dfii.sort_values(by=['численность'], ascending=False, inplace=True)
    mujeres = dfii['страна'].to_list()
    lugar_mujeres = mujeres.index(pais_elegido)+1, round(dfii[dfii['страна']==pais_elegido]['численность'].iat[0]*10**(-6), 1)
    
    dfii = dfi[['страна', 'численность']].groupby(by=['страна'], as_index=False).sum()
    dfii.sort_values(by=['численность'], ascending=False, inplace=True)
    total = dfii['страна'].to_list()
    lugar_total = total.index(pais_elegido)+1, round(dfii[dfii['страна']==pais_elegido]['численность'].iat[0]*10**(-6), 1)
    
    return 'Население: '+str(lugar_total[0])+'-е место ('+str(lugar_total[1])+' млн чел.)', \
        'Мужчины: '+str(lugar_hombres[0])+'-е место ('+str(lugar_hombres[1])+' млн чел.)', \
        'Женщины: '+str(lugar_mujeres[0])+'-е место ('+str(lugar_mujeres[1])+' млн чел.)'
    



@app.callback(Output('din_gender', 'figure'), Input('slider2', 'value'))
def f_din_gender(grupos):
    lista_edades3 = lista_edades2[grupos[0]:grupos[1]+1]
    dfi = df2[(df2['страна']==pais_elegido) & (df2['возраст'].isin(lista_edades3)) &(df2['пол'].isin(['мужской', 'женский']))]
    dfi = dfi[['год', 'пол', 'численность']].groupby(by=['год', 'пол'], as_index=False).sum()
    dfi.loc[dfi['пол']=='женский', 'численность'] = -1*dfi['численность']
    
    fig = px.line(
        dfi,
        x='год',
        y='численность',
        markers=True,
        color='пол',
        color_discrete_map={'мужской':'#00FFFF', 'женский':'#FF69B4'},
        height=300,
        labels={'численность':'численность населения'}
        
        )

    fig.layout.template = 'plotly_dark'
    fig.update_traces(line={'width': 3}, marker={'size':10, 'symbol':'hexagon'})
    fig.update_layout(margin={'l':0, 'b':0, 't':0, 'r':0})    

    return fig



@app.callback(Output('fig1_poblacion', 'figure'), 
              Input('lista_paises', 'value'))
def f_din_de_pobl(pais_i):
    if not pais_i: pais_i = []

    dfi = df[(df['страна'].isin([pais_elegido]+pais_i)) &  
             (df['пол']=='Total') &
             (df['возраст']=='TOTAL')]
    fig = px.line(dfi,
                  x='год',
                  y='численность',
                   height=395, #width=600,
                  markers=True,
                  color='страна',
                  labels={'численность':'численность населения'}
                      )
    fig.layout.template = 'plotly_dark'
    fig.update_traces(line={'width': 3}, marker={'size':10, 'symbol':'hexagon'})
    fig.update_layout(margin={'l':0, 'b':0, 't':20, 'r':0})
    
    return fig



@app.callback(Output('fig2_gender', 'figure'),
              Output('fig3_gender', 'figure'),
              Input('slider1', 'value'))
def f_gender_pyramida(ano):
    # df2.loc[df2['пол']=='женский', '% в группе'] = -1*df2['% в группе']
    # df2.loc[df2['пол']=='женский', 'численность'] = -1*df2['численность']
    
    fig2 = px.bar(df2[(df2['страна']==pais_elegido) & (df2['год']==ano) &(df2['пол'].isin(['мужской', 'женский']))],
                  x='численность',
                  y='возраст',
                  color='пол',
                  # color_discrete_sequence=['#00FFFF', '#FF69B4'],
                  color_discrete_map={'мужской':'#00FFFF', 'женский':'#FF69B4'},
                  orientation='h',
                  # range_x=[-100, 100],
                  height=395,
                  barmode='relative',
                  
                  
                  
                  )
    fig2.layout.template = 'plotly_dark'
    fig2.layout.yaxis={'side':'right'}
    fig2.layout.legend={'x':-0.2}
    fig2.layout.title={'x':0.5, 'text':str(ano) + ' год'}
    fig2.layout.annotations = [{'text':'возраст', 'showarrow':False, 'xref':'paper', 'x':1.12, 'yref':'paper', 'y':1.1, 'font':{'size':14}}]

    # fig3
    fig3 = px.bar(df2[(df2['страна']==pais_elegido) & (df2['год']==ano) &(df2['пол'].isin(['мужской']))],
                  x='перекос',
                  y='возраст',
                   color='цвет',
                  # color_discrete_sequence=['#00FFFF', '#FF69B4'],
                  color_discrete_map={'мужской':'#00FFFF', 'женский':'#FF69B4'},
                  height=395,
                  orientation='h',
                  # title=' '
                  # barmode='overlay'
                  # range_x=[-100, 100],
                  # barmode='relative'
                  
                  ) 
    fig3.layout.yaxis={'visible':False, 'categoryorder':"category ascending"}
    fig3.layout.legend={'visible':False}
    fig3.update_layout(margin={'l':0, 'r':0})
    fig3.layout.template = 'plotly_dark'


    return fig2, fig3      
            





app.layout = maqueta_general

if __name__=='__main__':
    
    app.run_server(debug=False, port=8050)























