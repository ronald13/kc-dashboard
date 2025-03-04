import pandas as pd
import plotly.graph_objects as go
import numpy as np
from dash import html
from collections import Counter
import math


MAFIA_COLOR = '#295883'
CITIZEN_COLOR = '#f24236'
SHERIFF_COLOR = '#cbe5f3'
DON_COLOR = '#efbf00'

GREEN_COLOR = '#49A078'

def get_role():
    role = pd.DataFrame([{'role_id': 1, 'role_name': 'Мирный', 'short_name': 'Мир',  'color': '#f24236'}, {'role_id': 2, 'role_name': 'Мафия', 'short_name': 'Маф', 'color': '#295883'},
                         {'role_id': 3, 'role_name': 'Дон', 'short_name': 'Дон', 'color': '#efbf00'}, {'role_id': 4, 'role_name': 'Шериф', 'short_name': 'Шер', 'color': '#cbe5f3'}])
    return role


def calcilate_Ci(row):
    """
    Рассчитывает значение Ci на основе условий для строки DataFrame.
    """
    # Константа для сравнения даты
    date_threshold = pd.to_datetime('2024-05-25')

    # Вычисление базового full_Ci
    if row['game_date'] >= date_threshold:
        full_Ci = row['total_kill_in_series'] * 0.6 / 2
    else:
        full_Ci = row['total_kill_in_series'] * 0.4 / 2

    # Определение множителя на основе условий
    if row['maf_in_best'] >= 1 and row['who_win'] == 1:
        modifier = 1
    elif row['maf_in_best'] >= 1 and row['who_win'] == 0:
        modifier = 0.5
    elif row['maf_in_best'] == 0 and row['who_win'] == 1:
        modifier = 0.5
    elif row['maf_in_best'] == 0 and row['who_win'] == 0:
        modifier = 0.25
    else:
        modifier = 0  # На случай, если ни одно условие не выполнено (защитный код)

    # Итоговое значение Ci
    return full_Ci * modifier


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
    df_games['game_date'] = pd.to_datetime(df_games['game_date'])

    df_firstshots = pd.json_normalize(
    [game['gamefirstshot'] for game in data if 'gamefirstshot' in game]
    )
    df_firstshots.rename(columns={'score': 'score_firstshot'}, inplace=True)

    best_roles_dict = df_games[df_games['marked_in_best'] == 1].groupby('game_id')['role_id'].agg(list).to_dict()
    # Применяем словарь к датафрейму
    df_games['best_roles'] = df_games['game_id'].map(best_roles_dict)

    # Функция для подсчета мафиозных ролей с обработкой NaN
    def count_mafia_roles(roles):
        if isinstance(roles, list):
            return sum(1 for role in roles if role in [2, 3])
        return 0

    # Добавляем столбец с подсчетом мафиозных ролей среди лучших игроков
    df_games['maf_in_best'] = df_games['best_roles'].apply(count_mafia_roles)

    # Добавляем столбец с который показывает
    df_games['win_condition'] = np.where(
        ((df_games['role_id'].isin([1, 4])) & (df_games['who_win'] == 0)) |
        ((df_games['role_id'].isin([2, 3])) & (df_games['who_win'] == 1)),
        1,
        0
    )

    df_firstshots = df_firstshots.merge(df_games[
                                            ['game_id', 'game_date', 'player_id', 'player_name', 'role_id', 'who_win',
                                             'best_roles', 'maf_in_best']],
                                        on=['game_id', 'player_id'], how='left')

    # добавляем столбец total_kill_in_series чтобы посчитать общее количество убийств игрока в серии
    df_firstshots['total_kill_in_series'] = df_firstshots.groupby(['game_date', 'player_name'])['game_id'].transform(
        'count')
    # df_firstshots['game_date'] = pd.to_datetime(df_firstshots['game_date'])


    df_firstshots['Ci'] = df_firstshots.apply(calcilate_Ci, axis=1)

    df_games = df_games.merge(df_firstshots[['game_id', 'player_id', 'score_firstshot', 'Ci']],
                              on=['game_id', 'player_id'], how='left')

    df_games['score_firstshot'] = df_games['score_firstshot'].fillna(0)
    df_games['Ci'] = df_games['Ci'].fillna(0)

    df_games['score'] = df_games['score'].astype(float)
    df_games['score_dop'] = df_games['score_dop'].astype(float)
    df_games['score_minus'] = df_games['score_minus'].astype(float)
    df_games['score_firstshot'] = df_games['score_firstshot'].astype(float)

    df_games['only_dops'] = df_games['score_dop'] + df_games['score_minus'] + df_games['score_firstshot']

    df_games['total_score'] = df_games['score'] + df_games['score_dop'] + df_games['score_minus'] + df_games[
        'score_firstshot'] + df_games['Ci']


    # add place for player in series




    return df_games, df_firstshots


def create_timeline(df, selected_player=None):
    # Преобразование строковых дат в формат datetime
    # df['game_date'] = pd.to_datetime(df['game_date'])
    df.sort_values(by=['game_date', 'total_score'], ascending=[True, True] , inplace=True)

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

        # Создаем маску для первых мест (предполагая, что у вас есть колонка 'place' или аналогичная)
        # Замените 'place' на вашу колонку, которая указывает на место игрока
        first_place_mask = (df['player_name'] == selected_player) & (df['place_in_series'] == 1)
        selected_player_mask = df['player_name'] == selected_player
        colors = np.select(
            [first_place_mask, selected_player_mask],
            ['#f99746', '#f24236'],  # Золотой для первых мест, красный для выбранного игрока
            default='#e5e7eb'  # Серый для остальных
        )
    else:
        colors = '#f24236'


    fig_timeline = go.Figure()

    # Добавляем точки на график
    fig_timeline.add_trace(
        go.Scatter(
            x=x_coords,
            y=y_coords,
            mode='markers',
            marker=dict(
                color=colors,
                size=14,
                line=dict(color='#f24236', width=0)
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

    start_date = df['game_date'].min()
    end_date = df['game_date'].max()

    # Даты для вертикальных линий (начало каждого месяца)
    month_lines = pd.date_range(start=start_date.replace(day=1),
                               end=end_date,
                               freq='MS')

    # Даты для меток (середина каждого месяца)
    month_labels = pd.date_range(start=start_date.replace(day=1),
                                end=end_date,
                                freq='MS')
    # Сдвигаем метки на середину месяца
    month_labels = month_labels + pd.Timedelta(days=14)  # примерно середина месяца

    # Добавляем вертикальные линии для каждого месяца
    for date in month_lines[1:]:

        fig_timeline.add_vline(
            x=date,
            line_width=1,
            line_dash="dash",
            line_color="gray",
            opacity=0.5
        )

    # Настройка осей и внешнего вида
    fig_timeline.update_layout(
        margin={'t': 10, 'b': 10, 'l': 10, 'r': 0},
        dragmode=False,
        xaxis=dict(
            showticklabels=True,
            tickmode='array',
            ticktext=[d.strftime('%B %Y') for d in month_labels[1:]],
            tickvals=month_labels[1:],  # используем сдвинутые даты для меток
            tickangle=0,
            tickfont=dict(size=12),
            showgrid=False,
            fixedrange = True,
            range=['2024-03-23 00:00:00', '2025-01-29 00:00:00']
        ),
        yaxis=dict(
            title='',
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            fixedrange=True
        ),
        showlegend=False,
        height=200,
    )

    # fig_timeline.add_annotation(
    #     x='2024-03-26 00:00:00',
    #     y=-4,
    #     text='Скролл вправо',
    #     showarrow=False,
    #     bgcolor='#ffffff',
    #     opacity=0.8
    # )

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
                html.Span(f'{role["short_name"]} {role["count"]}%')
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

def create_winrate_distibution(df):
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
                html.Span(f'{role["short_name"]} {role["proportion"]}%')
            ], className='legend-item', style={'margin-bottom':4})
        )

    layout = html.Div([
        html.Div([
            # Легенда
            html.Div(legend_items, className='legend-column')

        ], className='container')
    ])
    return layout

def create_shooting_target(values):

    values = [x for x in values if not math.isnan(x)]
    counts = Counter(values)

    # Создаем случайные координаты для точек на круге
    n_points = len(values)
    np.random.seed(42)
    angles = np.random.uniform(0, 2 * np.pi, n_points)
    # Инвертируем значения и используем их как радиус
    radii = [3 - val for val in values]  # 3 в центре, 0 на краю

    # Преобразуем полярные координаты в декартовы
    x = [r * np.cos(theta) for r, theta in zip(radii, angles)]
    y = [r * np.sin(theta) for r, theta in zip(radii, angles)]

    # Создаем фигуру
    fig = go.Figure()

    # Добавляем круги мишени
    for r in [1, 2]:
        circle_points = 100
        theta = np.linspace(0, 2 * np.pi, circle_points)
        fig.add_trace(go.Scatter(
            x=r * np.cos(theta),
            y=r * np.sin(theta),
            mode='lines',
            line=dict(color='gray', width=1),
            showlegend=False,
            hoverinfo='skip'
        ))

    # Добавляем оси
    fig.add_trace(go.Scatter(
        x=[-3, 3], y=[0, 0],
        mode='lines',
        line=dict(color='gray', width=1, dash='dash'),
        showlegend=False,
        hoverinfo='skip'
    ))
    fig.add_trace(go.Scatter(
        x=[0, 0], y=[-3, 3],
        mode='lines',
        line=dict(color='gray', width=1, dash='dash'),
        showlegend=False,
        hoverinfo='skip'
    ))

    # Добавляем точки
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='markers',
        marker=dict(
            size=14,
            color=values,
            colorscale=['#f24236', '#295883', '#efbf00', '#cbe5f3'],
            showscale=False,
            # colorbar=dict(
            #     title='Значение',
            #     ticktext=['0', '1', '2', '3'],
            #     tickvals=[0, 1, 2, 3]
            # )
            cmin=0,  # Устанавливаем минимальное значение цветовой шкалы
            cmax=3  # Устанавливаем максимальное значение цветовой шкалы
        ),
        text = [f'{int(val)} {"черный" if int(val) == 1 else "черных"} в ЛХ<br>Всего: {counts[val]}' for val in values],
        hoverinfo='text'
    ))

    # Настраиваем макет
    fig.update_layout(
        margin={'t': 10, 'r': 10, 'l': 10, 'b': 10},
        dragmode=False,
        xaxis=dict(
            range=[-3.5, 3.5],
            zeroline=False,
            showgrid=False,
            showticklabels=False,
            fixedrange=True

        ),
        yaxis=dict(
            range=[-3.5, 3.5],
            zeroline=False,
            showgrid=False,
            showticklabels=False,
            scaleanchor='x',  # делаем круги круглыми
            scaleratio=1,
            fixedrange=True
        ),
        width=250,
        height=250,
        showlegend=False
    )
    return fig


def create_box_bars(values, param='#dsdss'):
    # Найдем индекс максимального значения
    max_index = np.argmax(values)

    # Создадим список цветов: подсветим бар с максимальным значением
    colors = [param] * len(values)
    colors[max_index] = '#f24236'  # Подсвечиваем максимальное значение

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        y=values,
        marker_color=colors,  # Используем список цветов
        name='expenses',
        hovertemplate='Бокс: ' + '<b>%{x}</b>' + '<br>' +
                      'Отстрел: ' + '<b>%{y}</b>' +
                      '<extra></extra>',
    ))

    fig.update_traces(
        texttemplate=['%{y}' if x > 0 else '' for x in values],
        textposition='outside'
    )

    fig.update_yaxes(visible=False, range=[0, max(values) + 4])
    fig.update_xaxes(
        range=[0.5, 10.5],
        zeroline=False,
        showgrid=False,
        linecolor='grey',
        linewidth=2,
        tickfont_size=10,
        tickmode="array",
        tickvals=np.arange(1, 11, 1),
        ticktext=[str(x) for x in range(1, 11)],
        fixedrange=True,
        tickangle=0
    )

    fig.update_layout(
        xaxis_fixedrange=True, yaxis_fixedrange=True,
        height=150,
        margin={'t': 10, 'r': 10, 'l': 10, 'b': 10, 'pad': 0},
        showlegend=False,
    )

    return fig


def get_box_color(box_data, df, metric):
    if metric == 'win_rate':
        value = box_data['win_rate_num']
        max_val = df['win_rate_num'].max()
        min_val = df['win_rate_num'].min()
    else:  # shots
        value = box_data['shots']
        max_val = df['shots'].max()
        min_val = df['shots'].min()

    if value == max_val:
        return GREEN_COLOR  # Зеленый для максимума
    elif value == min_val:
        return CITIZEN_COLOR  # Красный для минимума
    return SHERIFF_COLOR  # Станда

def create_circular_layout(df, selected_metrics):
    # Рассчитываем координаты для размещения боксов по кругу
    n_boxes = len(df)
    radius = 0.92
    start_angle = -np.pi / 2 - np.pi / 10
    angles = np.linspace(start_angle, start_angle + 2 * np.pi, n_boxes, endpoint=False)

    # Инвертируем порядок углов для движения по часовой стрелке
    angles = angles[::-1]

    x_coords = radius * np.cos(angles)
    y_coords = radius * np.sin(angles)

    fig = go.Figure()

    # Добавляем центральный стол
    fig.add_shape(
        type="circle",
        x0=-0.5, y0=-0.5,
        x1=0.5, y1=0.5,
        fillcolor="lightgray",
        line_color="gray",
    )

    # Добавляем боксы
    for i, (x, y) in enumerate(zip(x_coords, y_coords)):
        box_data = df.iloc[i]
        # Определяем цвет бокса на основе выбранных метрик
        box_color = "#574964"  # Standart box color

        if selected_metrics:
            for metric in selected_metrics:
                new_color = get_box_color(box_data, df, metric)
                if new_color != SHERIFF_COLOR:  # Если найден экстремум
                    box_color = new_color
                    break
        # Добавляем бокс
        fig.add_trace(go.Scatter(
            x=[x],
            y=[y],
            mode='markers+text',
            marker=dict(
                size=30,
                color=box_color,
                line=dict(color='rgb(25, 25, 25)', width=2)
            ),
            text=str(box_data['boxNumber'].astype(int)),
            textposition="middle center",
            textfont=dict(size=12, color='white'),
            hoverinfo='skip',
            name=f'Box {box_data["boxNumber"].astype(int)}'
        ))

        # Добавляем аннотации для метрик
        annotation_text = []
        if 'win_rate' in selected_metrics:
            annotation_text.append(f"<b>{box_data['win_rate']}%</b>")
        if 'shots' in selected_metrics:
            annotation_text.append(f"Убит: <b>{box_data['shots'].astype(int)}</b>")

        if annotation_text:
            # Рассчитываем позицию для аннотации (немного дальше от бокса)
            annotation_radius = radius * 1.2
            ann_x = annotation_radius * np.cos(angles[i])
            ann_y = annotation_radius * np.sin(angles[i])

            fig.add_annotation(
                x=ann_x,
                y=ann_y,
                text='<br>'.join(annotation_text),
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor='#636363',
                # color='#000',
                ax=x * 40,
                ay=-y * 40,
                bordercolor='#c7c7c7',
                borderwidth=2,
                borderpad=4,
                bgcolor='#ffffff',
                opacity=0.8
            )

    # Настраиваем внешний вид
    fig.update_layout(
        margin={'t': 0, 'r': 0, 'l': 0, 'b': 10},
        showlegend=False,
        dragmode=False,
        plot_bgcolor='white',
        width=340,
        height=340,
        xaxis=dict(
            range=[-2, 2],
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            fixedrange=True
        ),
        yaxis=dict(
            range=[-2, 2],
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            fixedrange=True
        ),

    )

    return fig


def number_win_series(df):
    # Шаг 1: Группируем по game_date и player_name и считаем сумму total_score
    summed_scores = df.groupby(['game_date', 'player_name'], as_index=False)['total_score'].sum()

    # Для каждого 'game_date' находим игрока с максимальным 'total_score'
    max_scores = summed_scores.loc[summed_scores.groupby('game_date')['total_score'].idxmax()]
    return max_scores['player_name'].value_counts().reset_index(name='count')

def generate_quadrant_plot(df, colors=['#f24236', '#295883', '#efbf00', '#cbe5f3']):
    """
    Создает Plotly-график с квадратами в каждой четверти.

    :param values: Список из 4 значений (проценты 0-100).
    :param names: Список из 4 названий (Q1-Q4).
    :param colors: Список из 4 цветов.
    :return: Объект figure для Dash.
    """
    assert len(df['winrate']) == 4 and len(df['role_name']) == 4 and len(df['color']) == 4, "Должно быть ровно 4 значения, имени и цвета."

    # Масштабирование размеров квадратов
    max_size = 1.0
    sizes = (np.array(df['winrate']) / 100) * max_size

    # Определение координат (чтобы один угол был в (0,0))
    quadrants = [
        [(0, 0), (-sizes[0], 0), (-sizes[0], sizes[0]), (0, sizes[0])],  # Q2 (Мирный)
        [(0, 0), (sizes[1], 0), (sizes[1], sizes[1]), (0, sizes[1])],    # Q1 (Мафия)
        [(0, 0), (-sizes[2], 0), (-sizes[2], -sizes[2]), (0, -sizes[2])], # Q3 (Дон)
        [(0, 0), (sizes[3], 0), (sizes[3], -sizes[3]), (0, -sizes[3])],   # Q4 (Шериф)
    ]

    fig = go.Figure()

    for i in range(4):
        x_coords, y_coords = zip(*quadrants[i])  # Разделяем X и Y координаты

        # Добавляем квадрат (убираем точки)
        fig.add_trace(go.Scatter(
            x=x_coords,
            y=y_coords,
            fill="toself",
            fillcolor=colors[i],
            line=dict(color="#bfc0c3", width=1),
            mode="lines",
            hoverinfo="text",
            text=f"<b>{df['role_name'][i]}</b><br>{df['win_games'][i]} из {df['total_games'][i]}<br><b>ДБ:</b> {df['dops'][i]}",
            name=df['role_name'][i],
            showlegend=False
        ))

        # Коррекция координат текста (40% от размера квадрата)
        text_x = x_coords[2] / 2  # 40% внутрь квадрата
        text_y = y_coords[2]  / 2

        if df['winrate'][i] >= 35:
            fig.add_trace(go.Scatter(
                x=[text_x],
                y=[text_y],
                text=[f"{df['winrate'][i]}%"],  # Только значение!
                mode="text",
                textfont=dict(size=9, color="white"),
                # hoverinfo="text",  # Оставляем hover только в центре квадрата
                hoverinfo="skip",


                showlegend=False
            ))

    # Настройки осей и стиля
    fig.update_layout(
        margin={'t': 0, 'r': 0, 'l': 0, 'b': 0},
        dragmode=False,
        xaxis=dict(zeroline=False,  showticklabels=False,  showgrid=False, range=[-1, 1],  fixedrange=True),
        yaxis=dict(zeroline=False, showticklabels=False,   showgrid=False, range=[-1, 1],  fixedrange=True),
        showlegend=False,

        # width=160,
        # height=160
    )

    return fig

def shorten_name(name, max_length=4):
    """Сокращает имя до указанной длины, сохраняя начало имени"""
    if len(name) <= max_length:
        return name
    return name[:max_length] + '.'

def get_colorscale(role):
    """Возвращает цветовую схему в зависимости от роли"""
    if role == 'Мирные':
        return [
            [0, 'rgb(255,240,240)'],      # Очень светлый пастельный розовый
            [0.25, 'rgb(255,218,218)'],   # Светлый пастельный розовый
            [0.5, 'rgb(255,182,182)'],    # Средний пастельный розовый
            [0.75, 'rgb(255,150,150)'],   # Пастельный розовый
            [1, 'rgb(255,105,105)']       # Более насыщенный пастельный розовый
        ]
    else:  # для Мафии
        return [
            [0, 'rgb(240,240,240)'],      # Очень светлый серый
            [0.25, 'rgb(180,180,180)'],   # Светлый серый
            [0.5, 'rgb(120,120,120)'],    # Средний серый
            [0.75, 'rgb(80,80,80)'],      # Темно-серый
            [1, 'rgb(40,40,40)']          # Очень темный серый
        ]

def create_heatmap(df, role='Мирные', min_winrate=0,  min_games=0):
    ## Фильтруем данные по роли, винрейту и количеству игр
    df_filtered = df[
        (df['role_group'] == role) &
        (df['win_rate'] >= min_winrate) &
        (df['total_games'] >= min_games)
        ].copy()

    # Получаем уникальные имена игроков
    players = sorted(list(set(df_filtered['player1_name'].unique()) |
                          set(df_filtered['player2_name'].unique())))

    # Создаем словарь для соответствия полных и сокращенных имен
    short_names = {name: shorten_name(name) for name in players}
    players_short = [short_names[name] for name in players]

    # Создаем пустые матрицы для винрейта и количества игр
    n = len(players)
    winrate_matrix = pd.DataFrame(None, index=players, columns=players)
    games_matrix = pd.DataFrame(None, index=players, columns=players)

    # Заполняем матрицы данными
    for _, row in df_filtered.iterrows():
        p1, p2 = row['player1_name'], row['player2_name']
        winrate_matrix.loc[p1, p2] = row['win_rate']
        winrate_matrix.loc[p2, p1] = row['win_rate']
        games_matrix.loc[p1, p2] = row['total_games']
        games_matrix.loc[p2, p1] = row['total_games']


    # # Получаем цветовую схему в зависимости от роли
    colorscale = get_colorscale(role)

    # Создаем тепловую карту
    fig = go.Figure(data=go.Heatmap(
        z=winrate_matrix.values,
        x=players,  # Используем сокращенные имена для осей
        y=players,
        text=games_matrix.values,
        texttemplate="%{text}",
        textfont={"size": 10},
        hoverongaps=False,

        hovertemplate="<b>%{y} - %{x}</b><br>" +
                      "Винрейт: %{z:.1f}%<br>" +
                      "Всего игр: %{text}<br><extra></extra>",
        colorscale=colorscale,
        showscale=False,
        xgap=2,
        ygap=2
    ))
    # Настраиваем layout
    fig.update_layout(
        margin={'t': 0, 'r': 5, 'l': 0, 'b': 0, 'pad': 15},
        width=465,
        height=350,
        dragmode=False,
        xaxis={
            'side': 'top',
            'position': 1,
            'tickangle': 0,
            'ticktext': players_short,  # Полные имена для оси X
            'tickvals': list(range(len(short_names))),  # Позиции для меток
            'tickfont': dict(
                size=11,
            ),
        },
        # yaxis={
        #
        # },

    )

    return fig

def create_sankey(df):
    # Создание нод для первого столбца - комбинация имени игрока и роли
    df['source_node'] = df['player1_name'] + ' ' + df['role_group']

    # Подготовка данных для Sankey диаграммы
    sources = []
    targets = []
    values = []

    # Уникальные значения для source_node (первый столбец)
    source_nodes = df['source_node'].unique().tolist()

    # Уникальные значения для player2_name (второй столбец)
    target_nodes = df['player2_name'].unique().tolist()

    # Создаем словарь для хранения win_rate для каждого target_node
    target_win_rates = {}

    # Рассчитываем общий процент выигрыша для каждого target игрока
    for target_node in target_nodes:
        player_rows = df[df['player2_name'] == target_node]
        # Если нужно средневзвешенное значение с учетом количества игр
        weighted_win_rate = sum(player_rows['win_rate'] * player_rows['total_games']) / sum(player_rows['total_games'])
        # Округляем до одного десятичного знака
        target_win_rates[target_node] = round(weighted_win_rate, 1)

    # Модифицируем target_nodes, добавляя процент выигрыша
    target_node_labels = [f"{node} ({target_win_rates[node]}%)" for node in target_nodes]

    # Создание словаря для маппинга названий нод на их индексы
    node_indices = {node: i for i, node in enumerate(source_nodes + target_nodes)}

    # Цвета для различных ролевых групп
    role_colors = {
        'Мирные': 'rgba(242, 66, 54, 0.6)',  # Синий для мирных
        'Мафия': 'rgba(41, 88, 131, 0.6)'  # Темно-красный для мафии
    }

    # Заполнение источников, целей и значений
    node_colors = []
    for source_node in source_nodes:
        role = source_node.split(' ')[-1]
        node_colors.append(role_colors.get(role, 'rgba(100, 100, 100, 0.8)'))

    # Добавляем цвета для target_nodes
    for target_node in target_nodes:
        # Можно варьировать оттенок в зависимости от win_rate
        win_rate = target_win_rates[target_node]
        # Например, чем выше процент, тем темнее оттенок
        opacity = min(0.3 + win_rate / 100, 0.9)  # от 0.3 до 0.9 в зависимости от win_rate
        node_colors.append(f'rgba(229, 231, 235, {opacity})')

    # Собираем данные для связей
    link_colors = []
    hover_data = []

    for _, row in df.iterrows():
        source_index = node_indices[row['source_node']]
        target_index = node_indices[row['player2_name']]
        sources.append(source_index)
        targets.append(target_index)
        values.append(row['win_rate'])

        # Цвет связи на основе роли
        role = row['role_group']
        link_colors.append(role_colors.get(role, 'gray'))

        # Данные для hover
        hover_data.append({
            'player2_name': row['player2_name'],
            'wins_together': row['wins_together'],
            'total_games': row['total_games'],
            'win_rate': row['win_rate']
        })

    # Создание Sankey диаграммы
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,  # Увеличил pad для лучшего восприятия на мобильных
            thickness=15,  # Увеличил толщину для лучшего таргетинга
            line=dict(color="black", width=0.5),
            label=source_nodes + target_node_labels,  # Используем modified_target_nodes с процентами
            color=node_colors,
            hoverinfo='none',  # Используем допустимое значение 'none'
            hoverlabel=dict(
                bgcolor="white",
                font_size=14,
                font_family="Arial"
            )
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors,
            hovertemplate='<b>%{customdata.player2_name}</b><br>Выиграно: <b>%{customdata.wins_together}</b> из <b>%{customdata.total_games}</b><br>Winrate: <b>%{customdata.win_rate}%</b><extra></extra>',
            customdata=hover_data,
            hoverlabel=dict(
                bgcolor="white",
                bordercolor="black",
                font_size=14,
                font_family="Arial"
            )
        ))])

    # Настройка макета
    fig.update_layout(
        margin={'t': 20, 'r': 10, 'l': 10, 'b': 20, 'pad': 15},
        dragmode='pan',  # Меняем на 'pan' для лучшего взаимодействия на мобильных
        font_size=13,
        hoverdistance=50,  # Увеличенное расстояние для активации ховера
        hovermode='closest',  # Режим ховера "ближайший" лучше работает на мобильных
        uirevision='true',  # Сохранение состояния при взаимодействии
        clickmode='event+select',  # Улучшенное взаимодействие при клике
        autosize=True
    )


    # Возвращаем фигуру
    return fig