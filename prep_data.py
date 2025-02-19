import pandas as pd


def analyze_pairs_optimized(df):
    """
    Оптимизированная функция для анализа игровых пар с группировкой по ролям.

    Parameters:
    df (pandas.DataFrame): Датафрейм с игровыми данными

    Returns:
    tuple: (полная статистика пар, агрегированная статистика по группам ролей)
    """
    # Создаем копии датафрейма для обоих игроков
    pairs_1 = df[['game_id', 'player_id', 'player_name', 'role_id', 'win_condition']].copy()
    pairs_2 = df[['game_id', 'player_id', 'player_name', 'role_id', 'win_condition']].copy()

    # Переименовываем столбцы для merge
    pairs_1.columns = ['game_id', 'player1_id', 'player1_name', 'role1', 'win_condition']
    pairs_2.columns = ['game_id', 'player2_id', 'player2_name', 'role2', 'win_condition']

    # Объединяем датафреймы для получения всех возможных пар в каждой игре
    pairs = pd.merge(pairs_1, pairs_2, on=['game_id', 'win_condition'])

    # Фильтруем, чтобы исключить пары игрока с самим собой
    pairs = pairs[pairs['player1_id'] != pairs['player2_id']]

    # Создаем маску для допустимых комбинаций ролей
    roles_mask = (
        # 1-1, 1-4, 4-1
        ((pairs['role1'] == 1) & (pairs['role2'].isin([1, 4]))) |
        ((pairs['role1'] == 4) & (pairs['role2'] == 1)) |
        # 2-2, 2-3, 3-2
        ((pairs['role1'] == 2) & (pairs['role2'].isin([2, 3]))) |
        ((pairs['role1'] == 3) & (pairs['role2'] == 2))
    )

    # Применяем фильтр ролей
    pairs = pairs[roles_mask]

    # Добавляем столбец с группой ролей
    def get_role_group(row):
        if row['role1'] in [1, 4] and row['role2'] in [1, 4]:
            return 'Мирные'
        elif row['role1'] in [2, 3] and row['role2'] in [2, 3]:
            return 'Мафия'
        else:
            return 'Другое'

    pairs['role_group'] = pairs.apply(get_role_group, axis=1)

    # Получаем детальную статистику по всем комбинациям
    detailed_stats = pairs.groupby([
        'player1_id', 'player1_name', 'role1',
        'player2_id', 'player2_name', 'role2'
    ]).agg({
        'game_id': 'count',
        'win_condition': 'sum'
    }).reset_index()

    # Переименовываем столбцы в детальной статистике
    detailed_stats = detailed_stats.rename(columns={
        'game_id': 'total_games',
        'win_condition': 'wins_together'
    })
    detailed_stats['win_rate'] = (detailed_stats['wins_together'] / detailed_stats['total_games'] * 100).round(2)

    # Получаем агрегированную статистику по группам ролей
    grouped_stats = pairs.groupby([
        'player1_id', 'player1_name',
        'player2_id', 'player2_name',
        'role_group'
    ]).agg({
        'game_id': 'count',
        'win_condition': 'sum'
    }).reset_index()

    # Переименовываем столбцы в агрегированной статистике
    grouped_stats = grouped_stats.rename(columns={
        'game_id': 'total_games',
        'win_condition': 'wins_together'
    })

    # Добавляем процент побед
    grouped_stats['win_rate'] = (grouped_stats['wins_together'] / grouped_stats['total_games'] * 100).round(2)

    # Сортируем по убыванию количества побед
    grouped_stats = grouped_stats.sort_values(['wins_together', 'win_rate'], ascending=[False, False])

    # # Создаем уникальный идентификатор пары игроков, сортируя имена
    # grouped_stats["pair_key"] = grouped_stats.apply(lambda row: tuple(sorted([row["player1_name"], row["player2_name"]])), axis=1)
    #
    # # Удаляем дубликаты по этому ключу, оставляя только первое вхождение
    # grouped_stats = grouped_stats.drop_duplicates(subset="pair_key").drop(columns=["pair_key"])

    return detailed_stats, grouped_stats