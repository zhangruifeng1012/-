import os
import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from config import Config

os.makedirs(Config.DATA_DIR, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            created_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bidding_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            url_hash TEXT UNIQUE,
            url TEXT,
            region TEXT,
            industry TEXT,
            publish_date TEXT,
            source TEXT,
            budget REAL,
            keywords TEXT,
            created_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            keyword TEXT,
            region TEXT,
            industry TEXT,
            created_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawl_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            keyword TEXT,
            url TEXT,
            status TEXT,
            result_count INTEGER,
            created_at TEXT,
            completed_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def url_exists(url_hash):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM bidding_data WHERE url_hash = ?', (url_hash,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def insert_bidding(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    url_hash = hashlib.md5(data.get('url', '').encode()).hexdigest() if data.get('url') else hashlib.md5(data.get('title', '').encode()).hexdigest()
    try:
        cursor.execute('''
            INSERT INTO bidding_data 
            (title, content, url_hash, url, region, industry, publish_date, source, budget, keywords, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('title', ''),
            data.get('content', ''),
            url_hash,
            data.get('url', ''),
            data.get('region', ''),
            data.get('industry', ''),
            data.get('publish_date', ''),
            data.get('source', ''),
            data.get('budget', 0),
            data.get('keywords', ''),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_bidding_list(region=None, industry=None, keyword=None, start_date=None, end_date=None, sort_by='date', page=1, per_page=20):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = 'SELECT * FROM bidding_data WHERE 1=1'
    params = []
    if region and region != 'all':
        query += ' AND region = ?'
        params.append(region)
    if industry:
        query += ' AND industry = ?'
        params.append(industry)
    if keyword:
        query += ' AND (title LIKE ? OR keywords LIKE ?)'
        params.extend([f'%{keyword}%', f'%{keyword}%'])
    if start_date:
        query += ' AND publish_date >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND publish_date <= ?'
        params.append(end_date)
    if sort_by == 'date':
        query += ' ORDER BY publish_date DESC'
    elif sort_by == 'budget':
        query += ' ORDER BY budget DESC'
    offset = (page - 1) * per_page
    query += ' LIMIT ? OFFSET ?'
    params.extend([per_page, offset])
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_bidding_count(region=None, industry=None, keyword=None, start_date=None, end_date=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = 'SELECT COUNT(*) as cnt FROM bidding_data WHERE 1=1'
    params = []
    if region and region != 'all':
        query += ' AND region = ?'
        params.append(region)
    if industry:
        query += ' AND industry = ?'
        params.append(industry)
    if keyword:
        query += ' AND (title LIKE ? OR keywords LIKE ?)'
        params.extend([f'%{keyword}%', f'%{keyword}%'])
    if start_date:
        query += ' AND publish_date >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND publish_date <= ?'
        params.append(end_date)
    cursor.execute(query, params)
    result = cursor.fetchone()
    conn.close()
    return result['cnt']

def get_trend_data(days=30):
    conn = get_db_connection()
    cursor = conn.cursor()
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT DATE(publish_date) as date, COUNT(*) as cnt, industry
        FROM bidding_data 
        WHERE publish_date >= ?
        GROUP BY DATE(publish_date), industry
        ORDER BY date
    ''', (start_date,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_region_distribution():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT region, COUNT(*) as cnt, AVG(budget) as avg_budget
        FROM bidding_data 
        GROUP BY region
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_industry_distribution():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT industry, COUNT(*) as cnt, SUM(budget) as total_budget
        FROM bidding_data 
        GROUP BY industry
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_keyword_analysis():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT keywords, title FROM bidding_data WHERE keywords IS NOT NULL AND keywords != ""')
    rows = cursor.fetchall()
    conn.close()
    word_freq = {}
    for row in rows:
        keywords = row['keywords'].split(',')
        for kw in keywords:
            kw = kw.strip()
            if kw:
                word_freq[kw] = word_freq.get(kw, 0) + 1
        title_words = row['title'].split()
        for w in title_words:
            if len(w) >= 2:
                word_freq[w] = word_freq.get(w, 0) + 1
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:50]
    return [{'word': w, 'count': c} for w, c in sorted_words]

def get_user_by_username(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_user(username, password, email=''):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (username, password, email, created_at)
            VALUES (?, ?, ?, ?)
        ''', (username, password, email, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def log_crawl_task(user_id, keyword, url, status, result_count=0):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO crawl_tasks (user_id, keyword, url, status, result_count, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, keyword or '', url or '', status, result_count, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def get_crawl_tasks(user_id, limit=10):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM crawl_tasks WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
    ''', (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_bidding_by_id(bid_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bidding_data WHERE id = ?', (bid_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None
