import pandas as pd
import plotly.graph_objects as go
import numpy as np
from dash import Dash, html
import dash_bootstrap_components as dbc


def get_role():
    role = pd.DataFrame([{'role_id': 1, 'role_name': 'Мирный', 'color': '#f24236'}, {'role_id': 2, 'role_name': 'Мафия', 'color': '#295883'},
                         {'role_id': 3, 'role_name': 'Дон', 'color': '#efbf00'}, {'role_id': 4, 'role_name': 'Шериф', 'color': '#cbe5f3'}])
    return role

def get_full_data(data):
    df_games = pd.json_normalize(
        data,
        record_path='gameplayer',
        meta=[
            'id', 'club_id', 'date', 'table', 'number',
            'winner_id', 'user_id', 'subscribe', 'coeff',
            'transa', 'active_fase', 'WinnerName'
        ],
        meta_prefix='gameplayer_',
        errors='ignore'
    )

    columns = ['game_id', 'gameplayer_date', 'gameplayer_club_id', 'player_id', 'PlayerName', 'role_id',
               'gameplayer_winner_id', 'boxNumber', 'score', 'score_dop', 'score_minus', 'best']


    col_for_remane = {'gameplayer_date': 'game_date', 'gameplayer_club_id': 'series_id', 'PlayerName': 'player_name',
           'gameplayer_winner_id': 'who_win', 'best': 'marked_in_best'}
    df_games = df_games[columns].rename(columns=col_for_remane)

    df_firstshots = pd.json_normalize(
    [game['gamefirstshot'] for game in data if 'gamefirstshot' in game]
    )
    df_firstshots.rename(columns={'score': 'score_firstshot'}, inplace=True)

    df_games = df_games.merge(df_firstshots[['game_id', 'player_id', 'score_firstshot']], on=['game_id', 'player_id'], how='left')
    df_games['score_firstshot'] = df_games['score_firstshot'].fillna(0)

    df_games['score'] = df_games['score'].astype(float)
    df_games['score_dop'] = df_games['score_dop'].astype(float)
    df_games['score_minus'] = df_games['score_minus'].astype(float)
    df_games['score_firstshot'] = df_games['score_firstshot'].astype(float)

    df_games['total_score'] = df_games['score'] + df_games['score_dop'] + df_games['score_minus'] + df_games[
        'score_firstshot']

    df_games['game_date'] = pd.to_datetime(df_games['game_date'])

    return df_games


def create_timeline(df, selected_player=None):
    # Преобразование строковых дат в формат datetime
    df['game_date'] = pd.to_datetime(df['game_date'])

    # Группировка по дате и подсчет количества событий на каждую дату
    grouped = df.groupby('game_date').size()

    # Создание координат для точек с симметрией
    x_coords = []
    y_coords = []

    for date, count in grouped.items():
        # Для чётного числа точек
        if count % 2 == 0:
            y_values = list(range(-count // 2, count // 2))
        else:  # Для нечётного числа точек
            y_values = list(range(-(count // 2), count // 2 + 1))

        x_coords.extend([date] * count)
        y_coords.extend(y_values)

    if selected_player:
        colors = np.where(df['player_name'] == selected_player, '#f24236', '#e5e7eb')
    else:
        colors = '#f24236'

        # Создание графика с помощью Plotly
    fig_timeline = go.Figure()

    # Добавляем точки на график
    fig_timeline.add_trace(
        go.Scatter(
            x=x_coords,
            y=y_coords,
            mode='markers',
            marker=dict(
                color=colors,
                size=16,
                line=dict(color='#f24236', width=2)
            ),
            customdata=np.stack(
                (df['player_name'].astype('str'),
                 df['total_score'].round(2).astype('str'),
                 df['game_count'].round(0).astype('str')),
                axis=-1),
            hovertemplate='<b>%{x}</b><br>' +
                          '%{customdata[0]}<br>'+
                          'Cыграно: <b>%{customdata[2]}</b> игр<br>' +
                          'Получено: <b>%{customdata[1]}</b> баллов' +
                          '<extra></extra>',
        )
    )

    # Настройка осей и внешнего вида
    fig_timeline.update_layout(
        margin={'t': 10, 'b': 10, 'l': 10, 'r': 10},
        xaxis=dict(
            showticklabels=False,
        ),
        yaxis=dict(
            title='',
            showticklabels=False
        ),
        showlegend=False,
        height=185,
    )

    # Добавление аннотаций для первой и последней даты
    first_date = df['game_date'].min().strftime('%Y-%m-%d')
    last_date = df['game_date'].max().strftime('%Y-%m-%d')
    #
    fig_timeline.add_annotation(
        x=first_date,
        y=0,
        text=first_date,
        showarrow=False,
        xshift=-50,  # Сдвиг аннотации влево
        yanchor="middle",
        font_size = 16
    )
    fig_timeline.add_annotation(
        x=last_date,
        y=0,
        text=last_date,
        showarrow=False,
        xshift=50,  # Сдвиг аннотации вправо
        yanchor="middle",
        font_size=16,

    )

    return fig_timeline

def winrate_chart(value):
    chart = html.Div([
        html.Div('% WIN',
                style={'margin-bottom': '10px'},
                 className='tite__title'
                 ),

        # Контейнер для прогресс-бара
        html.Div([
            # Красная полоса (60%)
            html.Div(className='progress-bar', style={'width': f"{value}%"}),
        ], className='progress-container'),

        # Подписи с процентами
        html.Div([
            html.Span(f"{value}%", style={'color': '#ef4444'}),
            html.Span('100%', style={'color': '#6b7280'})
        ], className='labels')

    ], className='container')
    return chart

def create_cart_distibution(df):
    # Создаем прогресс бары с накоплением
    bars = []
    current_position = 0
    for _, role in df.iterrows():
        # print(f"{role['count']}%")
        print(type(role['count']))
        bars.append(
            html.Div(
                className='progress-bar',
                style={
                    'left': f'{current_position}%',
                    'width': f'{role["count"]}%',
                    'background-color': role["color"]
                }
            )
        )
        # print(role.count, type(role.count))
        current_position += role['count']

    # Создаем элементы легенды
    legend_items = []
    for _, role in df.iterrows():
        legend_items.append(
            html.Div([
                html.Div(
                    className='legend-color',
                    style={
                        'background-color': role.color
                    }
                ),
                html.Span(f'{role["role_name"]} {role["count"]}%')
            ], className='legend-item')
        )

    layout = html.Div([
        html.Div([
            html.Div('Распределение вытянутых ролей',
                    style={'margin-bottom': '10px'},
                    className='tile__title'),

            # Контейнер для прогресс-бара
            html.Div(bars, className='progress-container'),

            # Легенда
            html.Div(legend_items,className='legend')

        ], className='container')
    ])
    return layout