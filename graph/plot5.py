import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import csv
import datetime as dt
from time import time
import os
import psycopg2 as sq
from sys import argv

what = argv[1]
nbday = int(argv[2])

con = sq.connect(dbname="trollo", user="jul")
cur = con.cursor()
plt.style.use('tableau-colorblind10')
fig = plt.figure()
ax = fig.add_subplot(111)

res = cur.execute(f"""
    with 
        date as  (select * from generate_series(NOW()-interval '{nbday}d', NOW() , interval '1d') as d)
    select
        date_trunc('day', date.d) as timestamp,
        percentile_cont(0.5) WITHIN GROUP ( order by score) as med,
        CASE WHEN count(*) > 0 then sum(posts.score)/count(*) ELSE 0 END as average,
        count(*) from posts, date
    where is_spam is not true and maybe_spam is false and posts.post::text ILIKE '%{what}%' and
    posts.created_at BETWEEN  date.d::timestamp - interval '1d' and date.d::timestamp
    group by date.d order by date.d asc ;

""")

data = pd.DataFrame(cur.fetchall())
data.columns = [ "timestamp", "median", "average", "count" ]
idx = pd.period_range(min(data["timestamp"]), max(data["timestamp"]))
data.reindex(idx, fill_value=0)
time = data["timestamp"]
#delta = (-data["timestamp"].shift(1)+data["timestamp"])
#ax.plot(time, data["tier"], label="33%ile")
#ax.plot(time, data["up_tier"], label="66%ile")
#ax.plot(time, data["median"], label="median")
color = 'tab:red'
ax.plot(time, data["count"],  color=color)
ax.set_ylabel('nombre de posts', color=color)
ax2=ax.twinx()

color = 'tab:blue'

ax2.plot(time, data["median"], color=color)
ax2.set_ylabel('score médian des posts', color=color)
#ax.plot(time, data["count"], label="count")
#ax.xaxis.set_major_formatter(mdates.DateFormatter('%a'))
fig.autofmt_xdate()
fig.tight_layout()
ax.legend(loc='upper left')
plt.title(f"Évolution du score pour le mot «{what}» sur une fenêtre mouvante de 24h sur ces {nbday} derniers jours")
plt.show()
