import dash
from dash import dcc, html, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os
import json

# --- Configurações Iniciais ---
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="Analytics Institucional IPAJM"
)

# Carregar dados
BASE_PATH = "/home/ubuntu/Analytics_Gabriel"
df = pd.read_parquet(os.path.join(BASE_PATH, 'data_processed.parquet'))

# --- Funções Auxiliares para Gráficos ---

def create_pie_chart(data, values, names, title):
    fig = px.pie(data, values=values, names=names, hole=0.4,
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_layout(
        margin=dict(t=30, b=0, l=0, r=0),
        title={'text': title, 'x': 0.5, 'xanchor': 'center'},
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
    )
    return fig

def create_bar_chart(data, x, y, title, color=None):
    fig = px.bar(data, x=x, y=y, title=title, color=color,
                 color_discrete_sequence=['#175414'])
    fig.update_layout(
        margin=dict(t=40, b=20, l=20, r=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis_title="",
        yaxis_title="",
        title={'x': 0.5, 'xanchor': 'center'}
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor='LightGray')
    return fig

# --- Layout do Dashboard ---

def get_header():
    return html.Div([
        dbc.Row([
            dbc.Col(html.H1("IPAJM | Analytics Institucional", className="header-title"), width=8),
            dbc.Col(html.Div("Atualizado em: 09/04/2026", style={'textAlign': 'right', 'fontSize': '0.9rem'}), width=4)
        ], className="header-container align-items-center")
    ])

def get_metrics_row(filtered_df):
    total = len(filtered_df)
    media_sal = filtered_df['VL_REMUNERACAO'].mean()
    media_idade = filtered_df['IDADE'].mean()
    contribuicao_total = filtered_df['VL_CONTRIBUICAO'].sum()
    
    return dbc.Row([
        dbc.Col(html.Div([
            html.Div(f"{total:,}".replace(',', '.'), className="metric-value"),
            html.Div("Total de Servidores", className="metric-label")
        ], className="card-container metric-card"), width=3),
        
        dbc.Col(html.Div([
            html.Div(f"R$ {media_sal:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), className="metric-value"),
            html.Div("Remuneração Média", className="metric-label")
        ], className="card-container metric-card"), width=3),
        
        dbc.Col(html.Div([
            html.Div(f"{media_idade:.1f} anos", className="metric-value"),
            html.Div("Idade Média", className="metric-label")
        ], className="card-container metric-card"), width=3),
        
        dbc.Col(html.Div([
            html.Div(f"R$ {contribuicao_total/1e6:,.1f}M".replace(',', 'X').replace('.', ',').replace('X', '.'), className="metric-value"),
            html.Div("Contribuição Total", className="metric-label")
        ], className="card-container metric-card"), width=3),
    ], className="mb-4")

app.layout = html.Div([
    get_header(),
    
    dbc.Container([
        # Filtros
        html.Div([
            dbc.Row([
                dbc.Col([
                    html.Label("Categoria:"),
                    dcc.Dropdown(
                        id='filter-category',
                        options=[{'label': i, 'value': i} for i in df['CATEGORIA'].unique()],
                        value=df['CATEGORIA'].unique().tolist(),
                        multi=True,
                        placeholder="Selecione a Categoria"
                    )
                ], width=4),
                dbc.Col([
                    html.Label("Sexo:"),
                    dcc.Dropdown(
                        id='filter-sex',
                        options=[{'label': i, 'value': i} for i in df['SEXO_DESC'].unique()],
                        value=df['SEXO_DESC'].unique().tolist(),
                        multi=True,
                        placeholder="Selecione o Sexo"
                    )
                ], width=4),
                dbc.Col([
                    html.Label("Órgão (Top 10):"),
                    dcc.Dropdown(
                        id='filter-orgao',
                        options=[{'label': i, 'value': i} for i in df['NO_ORGAO'].value_counts().head(10).index],
                        multi=True,
                        placeholder="Selecione o Órgão"
                    )
                ], width=4),
            ])
        ], className="filter-container"),
        
        # Métricas Dinâmicas
        html.Div(id='metrics-output'),
        
        # Gráficos Linha 1
        dbc.Row([
            dbc.Col(html.Div([
                html.Div("Distribuição por Categoria", className="chart-title"),
                dcc.Graph(id='graph-category-dist')
            ], className="card-container"), width=4),
            
            dbc.Col(html.Div([
                html.Div("Distribuição por Faixa Etária", className="chart-title"),
                dcc.Graph(id='graph-age-dist')
            ], className="card-container"), width=8),
        ]),
        
        # Gráficos Linha 2
        dbc.Row([
            dbc.Col(html.Div([
                html.Div("Remuneração Média por Órgão (Top 10)", className="chart-title"),
                dcc.Graph(id='graph-salary-orgao')
            ], className="card-container"), width=6),
            
            dbc.Col(html.Div([
                html.Div("Distribuição por Sexo", className="chart-title"),
                dcc.Graph(id='graph-sex-dist')
            ], className="card-container"), width=6),
        ]),
        
        # Tabela de Dados
        html.Div([
            html.Div("Detalhamento de Cargos e Médias", className="chart-title"),
            html.Div(id='table-output')
        ], className="table-container mb-5")
        
    ], fluid=True)
])

# --- Callbacks ---

@app.callback(
    [Output('metrics-output', 'children'),
     Output('graph-category-dist', 'figure'),
     Output('graph-age-dist', 'figure'),
     Output('graph-salary-orgao', 'figure'),
     Output('graph-sex-dist', 'figure'),
     Output('table-output', 'children')],
    [Input('filter-category', 'value'),
     Input('filter-sex', 'value'),
     Input('filter-orgao', 'value')]
)
def update_dashboard(categories, sexes, orgaos):
    # Filtragem
    dff = df[df['CATEGORIA'].isin(categories)]
    dff = dff[dff['SEXO_DESC'].isin(sexes)]
    if orgaos:
        dff = dff[dff['NO_ORGAO'].isin(orgaos)]
    
    # Métricas
    metrics = get_metrics_row(dff)
    
    # Gráfico 1: Categoria
    cat_counts = dff['CATEGORIA'].value_counts().reset_index()
    fig1 = create_pie_chart(cat_counts, 'count', 'CATEGORIA', "")
    
    # Gráfico 2: Faixa Etária
    age_order = ['<18', '18-25', '26-35', '36-45', '46-55', '56-65', '66-75', '>75']
    age_counts = dff['FAIXA_ETARIA'].value_counts().reindex(age_order).reset_index()
    fig2 = create_bar_chart(age_counts, 'FAIXA_ETARIA', 'count', "")
    
    # Gráfico 3: Salário por Órgão
    sal_orgao = dff.groupby('NO_ORGAO')['VL_REMUNERACAO'].mean().sort_values(ascending=False).head(10).reset_index()
    fig3 = create_bar_chart(sal_orgao, 'NO_ORGAO', 'VL_REMUNERACAO', "")
    fig3.update_layout(xaxis={'tickangle': 45})
    
    # Gráfico 4: Sexo
    sex_counts = dff['SEXO_DESC'].value_counts().reset_index()
    fig4 = create_pie_chart(sex_counts, 'count', 'SEXO_DESC', "")
    
    # Tabela
    table_df = dff.groupby('NO_CARGO').agg({
        'ID_SERVIDOR_MATRICULA': 'count',
        'VL_REMUNERACAO': 'mean',
        'IDADE': 'mean'
    }).reset_index().sort_values('ID_SERVIDOR_MATRICULA', ascending=False).head(15)
    
    table_df.columns = ['Cargo', 'Qtd Servidores', 'Remuneração Média', 'Idade Média']
    
    table = dash_table.DataTable(
        data=table_df.to_dict('records'),
        columns=[{"name": i, "id": i} for i in table_df.columns],
        style_header={'backgroundColor': '#175414', 'color': 'white', 'fontWeight': 'bold'},
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_as_list_view=True,
        page_size=10
    )
    
    return metrics, fig1, fig2, fig3, fig4, table

if __name__ == '__main__':
    # Em produção (PythonAnywhere), usaremos gunicorn
    app.run_server(debug=True, host='0.0.0.0', port=8050)
