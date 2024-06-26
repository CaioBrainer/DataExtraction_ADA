from flask import Flask, jsonify, request, render_template
import schedule
from utils import (update_db_silver, update_raw_db, check_valide_date, get_number_news_bd, load_db,
                   count_keyword_occurrences)
import calendar
from flask_wtf.csrf import CSRFProtect
import threading
import time


app = Flask(__name__, template_folder='templates')  # instância o método Flask
csrf = CSRFProtect(app)


# Routes
@app.route('/')
def homepage():
    return render_template("index.html")


# OK
@app.route('/allnews')
def all_news():
    query = "SELECT id, title, description FROM silver_db.news;"
    df_news = load_db(query)
    dict_news = df_news.to_dict(orient='records')
    return render_template("all_news.html", tabela=dict_news)


# OK
@app.route('/news_by_day')
def news_by_day():
    query = ("SELECT EXTRACT(month FROM publication_date) AS month, EXTRACT(day FROM publication_date) AS day, COUNT(*)"
             "FROM silver_db.news "
             "GROUP BY month, day "
             "ORDER by month, day;")
    df_news = load_db(query)
    df_news['day'] = df_news['day'].astype(int)
    df_news['month'] = df_news['month'].astype(int)
    dict_news = df_news.to_dict(orient='records')
    return render_template("news_by_day.html", tabela=dict_news)

# OK
@app.route('/news_by_month')
def news_by_month():
    query = ("SELECT EXTRACT(month FROM publication_date) AS month, COUNT(*) "
             "FROM silver_db.news "
             "GROUP BY month "
             "ORDER by month")
    df_news = load_db(query)
    df_news['month'] = df_news['month'].astype(int)
    dict_news = df_news.to_dict(orient='records')
    return render_template("news_by_month.html", tabela=dict_news)


# OK
@app.route('/news_by_year')
def news_by_year():
    query = ("SELECT EXTRACT(year FROM publication_date) AS year, COUNT(*) "
             "FROM silver_db.news "
             "GROUP BY year "
             "ORDER by year")
    df_news = load_db(query)
    df_news['year'] = df_news['year'].astype(int)
    dict_news = df_news.to_dict(orient='records')
    return render_template("news_by_year.html", tabela=dict_news)


@app.route('/news_by_author')
def news_by_author():
    query = ("""SELECT silver_db.authors.name, COUNT(silver_db.news.id) AS article_count
        FROM silver_db.news
        JOIN silver_db.authors ON silver_db.authors.id = news.author_id
        GROUP BY silver_db.authors.name
        ORDER BY article_count DESC""")
    df_news = load_db(query)
    dict_news = df_news.to_dict(orient='records')
    return render_template("news_by_author.html", tabela=dict_news)


@app.route('/news_by_source')
def news_by_source():
    query = ("""SELECT silver_db.sources.name, COUNT(silver_db.news.id) AS source_count
        FROM silver_db.news
        JOIN silver_db.sources ON silver_db.sources.id = news.source_id
        GROUP BY silver_db.sources.name
        ORDER BY source_count DESC;""")
    df_news = load_db(query)
    dict_news = df_news.to_dict(orient='records')
    return render_template("news_by_source.html", tabela=dict_news)



@app.route('/news_by_author_and_source')
def by_source():
    query = ("""SELECT silver_db.sources.name AS source, silver_db.authors.name AS author, COUNT(silver_db.news.id) AS count
        FROM silver_db.news
        JOIN silver_db.sources ON silver_db.sources.id = silver_db.news.source_id
        JOIN silver_db.authors ON silver_db.authors.id = silver_db.news.author_id
        GROUP BY silver_db.sources.name, silver_db.authors.name
        ORDER BY count DESC;""")
    df_news = load_db(query)
    dict_news = df_news.to_dict(orient='records')
    return render_template("source_author.html", tabela=dict_news)


@app.route('/news_by_id', defaults={'var_id': 1})
@app.route('/news_by_id/<int:var_id>')
def news_by_id(var_id):
    id = int(var_id)
    query = f"SELECT id, title, description FROM silver_db.news WHERE id={id};"
    df_news = load_db(query)
    df_news['id'] = df_news['id'].astype(int)
    dict_news = df_news.to_dict(orient='records')
    return render_template("news_by_id.html", tabela=dict_news)


@app.route('/query_count')
def news_by_query():
    query = "SELECT id, title, description FROM silver_db.news;"
    df_news = load_db(query)
    count_title, count_description = count_keyword_occurrences(df_news, ['apple', 'tesla', 'xiaomi'])
    return render_template("news_by_query.html", title_table=count_title,
                           description_table=count_description)


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(5)


if __name__ == "__main__":

    schedule.every().hour.at(":54").do(update_raw_db)
    schedule.every().day.at("21:58").do(update_db_silver)
    port = 5000

    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()

    try:
        app.run(port=port)

    except KeyboardInterrupt:
        print('Detected keyboard interrupt, stopping Flask...')
