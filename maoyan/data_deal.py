import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
# 加载数据
def load_data():
    # 加载电影票房
    open_filepath = 'D:\pythondata\\3、猫眼电影\\box_result.csv'
    movie_box = pd.read_csv(open_filepath)
    movie_box = movie_box[['电影id', '电影名称','首映日期','总票房']].drop_duplicates()
    # 加载电影信息
    open_filepath = 'D:\pythondata\\3、猫眼电影\\maoyan_movie.xlsx'
    movie_message = pd.read_excel(open_filepath,sheet_name='maoyan_movie')
    movie_message.columns = ['电影url','电影名称','电影题材','国家','上映时间','用户评分','电影简介','导演/演员/编剧']
    movie_message = movie_message[['电影url','电影题材','国家','用户评分','导演/演员/编剧']].copy()
    movie_message.drop_duplicates(inplace=True)
    movie_message['电影id'] = movie_message.apply(lambda x:x['电影url'].replace('https://maoyan.com/films/',''),axis=1)
    movie_message[['电影id']] = movie_message[['电影id']].apply(pd.to_numeric)
    # 合并电影信息和票房
    data = pd.merge(movie_box,movie_message,how='inner',on=['电影id'])
    return data

# 只筛选中国的电影
data = data[data['国家'].str.contains('中国')]
# 剔除空值
data = data.dropna(subset=["导演/演员/编剧"])
# 将演员列表从字段“导演/演员/编剧”中分割出来
data['演员'] = data.apply(lambda x:x['导演/演员/编剧'] if '演员' in x['导演/演员/编剧'] else None,axis=1)
data['演员list'] = data.apply(lambda x:  '，'.join(x['演员'].split('yyyyy')[1].split('xxxxx')[2:]) if pd.notnull(x['演员']) else None,axis=1)
# 剔除无演员列表的行
data = data.dropna(subset=["演员list"])
# 剔除无用字段
data.drop(['导演/演员/编剧'],axis=1,inplace=True)
data.drop(['演员'],axis=1,inplace=True)

# 拆分演员列表，并转置成一列
data = data.drop("演员list", axis=1).join(data["演员list"].str.split("，", expand=True).stack().reset_index(level=1, drop=True).rename("演员"))
# 剔除配音演员
data = data[~data['演员'].str.contains('配音')]
data['演员'] = data.apply(lambda x: x['演员'].split('饰：')[0] if '饰：' in x['演员'] else x['演员'], axis=1)
# 剔除分割演员名称错误的行
data = data[~data['演员'].str.contains('uncredited')]
data = data[~data['演员'].str.contains('voice')]
data = data[~data['演员'].str.contains('Protester')]
# 取每部电影的前四名演员，部分影片特殊
data_actor = data[['电影id','电影名称','演员']].drop_duplicates()
data_actor_top4 = data_actor[data_actor['电影名称']!='我和我的祖国'].groupby(['电影id','电影名称']).head(4)
data_actor_top10 = data_actor[data_actor['电影名称']=='我和我的祖国'].groupby(['电影id','电影名称']).head(10)
data_actor_top4 = pd.concat([data_actor_top4,data_actor_top10])
# 剔除外国演员
data_actor_top4['演员名字长度'] = data_actor_top4.apply(lambda x: len(x['演员']),axis=1)
data_actor_top4 = data_actor_top4[(data_actor_top4['演员名字长度']<=3)].copy()
data_actor_top4.drop("演员名字长度",axis = 1,inplace=True)
# 匹配

# 拆分电影题材
data = data.join(data["电影题材"].str.split(",",expand = True).stack().reset_index(level = 1,drop = True).rename("题材"))
# 取每位演员最擅长的电影题材TOP3
data_type_actor = data[['电影id','电影名称','演员','题材']].drop_duplicates().groupby(['演员', '题材']).agg({'电影id': 'count'}).reset_index().sort_values(['演员','电影id'],ascending=False)
data_type_actor = data_type_actor.groupby(['演员']).head(3)
data_type_actor = data_type_actor.groupby(['演员'])['题材'].apply(list).reset_index()
data_type_actor['题材'] = data_type_actor['题材'].apply(lambda x: ','.join(str(i) for i in list(set(x)) if str(i) != 'nan'))
data_type_actor.rename(columns={'题材': '演员_拿手题材'}, inplace=True)
data = pd.merge(data,data_type_actor,how='left',on=['演员'])

actor = result[['演员','总票房','用户评分']].drop_duplicates()
# 衍生字段：平均票房、大于10亿票房影片、大于10亿票房影片计分
actor['用户评分'] = actor.apply(lambda x:0 if x['用户评分']=='暂无评分' else x['用户评分'],axis=1)
actor['大于10亿票房影片数量'] = actor.apply(lambda x:1 if x['总票房']>100000 else 0,axis=1)
# 按照票房赋予分值
def goal(x):
    if x['总票房']<=100000:
        division_goal = 0
    elif x['总票房']<=200000:
        division_goal = 1
    elif x['总票房'] <= 300000:
        division_goal = 2
    elif x['总票房'] <= 400000:
        division_goal = 3
    elif x['总票房'] <= 500000:
        division_goal = 4
    else:
        division_goal = 5
    return division_goal
actor['大于10亿票房影片计分'] = actor.apply(goal,axis=1)
actor['电影数量'] = 1
actor['用户评分'] = pd.to_numeric(actor['用户评分'])
actor['大于10亿票房影片数量'] = pd.to_numeric(actor['大于10亿票房影片数量'])
actor['大于10亿票房影片计分'] = pd.to_numeric(actor['大于10亿票房影片计分'])
# 汇总
actor2 = actor.groupby(['演员']).agg({'总票房': 'sum',
                                    '大于10亿票房影片数量': 'sum',
                                    '大于10亿票房影片计分': 'sum',
                                    '电影数量': 'count',
                                    '用户评分':'mean',}).reset_index()
# 筛选影片数量大于1的行——只有一部影片的演员设为单样本，会影响标准化的结果
actor2 = actor2[actor2['电影数量']>1].reset_index(drop=True)

# 复制一份副本
actor_copy = actor2.copy()
# 标准化处理
scaler = StandardScaler()
numeric_features = actor2.dtypes[actor2.dtypes != 'object'].index
scaler.fit(actor2[numeric_features])
scaled = scaler.transform(actor2[numeric_features])
for i, col in enumerate(numeric_features):
    actor2[col] = scaled[:, i]
# 划分演员档次：权重求和，根据分值排序
result = actor2.apply(lambda x: x['总票房']+x['大于10亿票房影片数量']+x['大于10亿票房影片计分']+0.5*x['电影数量']+0.5*x['用户评分'],axis=1)
# # 划分演员档次——方法2：采用聚类算法，自动分成4个组
# actor_model = actor2[['总票房', '大于10亿票房影片数量', '大于10亿票房影片计分','电影数量','用户评分']].values
# y_pred = KMeans(n_clusters=4, random_state=9).fit_predict(actor_model)
# result2 = pd.Series(y_pred)
# 合并两种结果
model_actor_reuslt = pd.concat([actor_copy, result], axis=1)
model_actor_reuslt.rename(columns={0: '总分'},inplace=True)
model_actor_reuslt = model_actor_reuslt.sort_values('总分',ascending=False).reset_index(drop=True)
data = pd.merge(data,data_actor_top4,how='inner',on=['电影id','电影名称','演员'])
