from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from config import Config
from database import init_db, get_bidding_list, get_bidding_count, get_trend_data
from database import get_region_distribution, get_industry_distribution, get_keyword_analysis
from database import get_user_by_username, create_user, log_crawl_task, get_crawl_tasks
from database import get_bidding_by_id, insert_bidding
from crawler import crawler
from cache import cache
import hashlib
import os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'zhaobiao-secret-key-2024'

init_db()

def get_region_name(region_id):
    for r in Config.REGIONS:
        if r['id'] == region_id:
            return r['name']
    return region_id

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': '请先登录'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'})
        user = get_user_by_username(username)
        if user and user['password'] == hashlib.md5(password.encode()).hexdigest():
            session['user'] = {'id': user['id'], 'username': user['username']}
            return jsonify({'success': True, 'message': '登录成功', 'redirect': url_for('dashboard')})
        elif not user:
            create_user(username, hashlib.md5(password.encode()).hexdigest(), f'{username}@example.com')
            user = get_user_by_username(username)
            session['user'] = {'id': user['id'], 'username': user['username']}
            return jsonify({'success': True, 'message': '注册并登录成功', 'redirect': url_for('dashboard')})
        return jsonify({'success': False, 'message': '密码错误'})
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', regions=Config.REGIONS, industries=Config.INDUSTRIES, pages=Config.DEFAULT_PAGES)

@app.route('/list')
@login_required
def list_page():
    return render_template('list.html', regions=Config.REGIONS, industries=Config.INDUSTRIES)

@app.route('/analysis')
@login_required
def analysis():
    return render_template('analysis.html')

@app.route('/detail/<int:bid_id>')
@login_required
def detail(bid_id):
    item = get_bidding_by_id(bid_id)
    return render_template('detail.html', item=item)

@app.route('/api/crawl', methods=['POST'])
@login_required
def api_crawl():
    data = request.get_json()
    keyword = data.get('keyword', '').strip()
    url = data.get('url', '').strip()
    user_id = session['user']['id']
    if not keyword and not url:
        return jsonify({'success': False, 'message': '请输入关键词或URL'})
    if keyword and len(keyword) > 100:
        return jsonify({'success': False, 'message': '关键词过长'})
    results = []
    if url:
        if not crawler.validate_url(url):
            return jsonify({'success': False, 'message': 'URL格式无效，请检查'})
        crawl_result = crawler.crawl_by_url(url, keyword)
        if crawl_result.get('deduped'):
            log_crawl_task(user_id, keyword, url, 'duplicate', 0)
            return jsonify({'success': True, 'message': crawl_result['message'], 'count': 0, 'deduped': True})
        results = crawl_result.get('data', [])
        log_crawl_task(user_id, keyword, url, 'completed', crawl_result.get('count', 0))
        return jsonify({'success': True, 'message': crawl_result['message'], 'count': crawl_result.get('count', 0), 'data': results[:5]})
    else:
        results = crawler.crawl_by_keyword(keyword, max_items=15)
        log_crawl_task(user_id, keyword, '', 'completed', len(results))
        return jsonify({'success': True, 'message': f'成功获取{len(results)}条新数据', 'count': len(results), 'data': results[:5]})

@app.route('/api/bidding')
@login_required
def api_bidding():
    region = request.args.get('region', 'all')
    industry = request.args.get('industry', '')
    keyword = request.args.get('keyword', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    sort_by = request.args.get('sort_by', 'date')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    cache_key = f'bidding:{region}:{industry}:{keyword}:{start_date}:{end_date}:{sort_by}:{page}:{per_page}'
    cached = cache.get(cache_key)
    if cached:
        return jsonify({'success': True, 'from_cache': True, 'data': cached['data'], 'total': cached['total']})
    data = get_bidding_list(region, industry, keyword, start_date, end_date, sort_by, page, per_page)
    total = get_bidding_count(region, industry, keyword, start_date, end_date)
    for item in data:
        item['region_name'] = get_region_name(item.get('region', ''))
    result = {'success': True, 'from_cache': False, 'data': data, 'total': total}
    cache.set(cache_key, {'data': data, 'total': total}, ttl=300)
    return jsonify(result)

@app.route('/api/trend')
@login_required
def api_trend():
    days = int(request.args.get('days', 30))
    cache_key = f'trend:{days}'
    cached = cache.get(cache_key)
    if cached:
        return jsonify({'success': True, 'from_cache': True, 'data': cached})
    data = get_trend_data(days)
    cache.set(cache_key, data, ttl=600)
    return jsonify({'success': True, 'from_cache': False, 'data': data})

@app.route('/api/region-distribution')
@login_required
def api_region_distribution():
    cache_key = 'region_distribution'
    cached = cache.get(cache_key)
    if cached:
        return jsonify({'success': True, 'from_cache': True, 'data': cached})
    data = get_region_distribution()
    region_map = {r['id']: r['name'] for r in Config.REGIONS}
    for item in data:
        item['name'] = region_map.get(item['region'], item['region'])
    cache.set(cache_key, data, ttl=600)
    return jsonify({'success': True, 'from_cache': False, 'data': data})

@app.route('/api/industry-distribution')
@login_required
def api_industry_distribution():
    cache_key = 'industry_distribution'
    cached = cache.get(cache_key)
    if cached:
        return jsonify({'success': True, 'from_cache': True, 'data': cached})
    data = get_industry_distribution()
    industry_map = {i['id']: i['name'] for i in Config.INDUSTRIES}
    for item in data:
        item['name'] = industry_map.get(item['industry'], item['industry'])
    cache.set(cache_key, data, ttl=600)
    return jsonify({'success': True, 'from_cache': False, 'data': data})

@app.route('/api/keyword-analysis')
@login_required
def api_keyword_analysis():
    cache_key = 'keyword_analysis'
    cached = cache.get(cache_key)
    if cached:
        return jsonify({'success': True, 'from_cache': True, 'data': cached})
    data = get_keyword_analysis()
    cache.set(cache_key, data, ttl=600)
    return jsonify({'success': True, 'from_cache': False, 'data': data})

@app.route('/api/tasks')
@login_required
def api_tasks():
    user_id = session['user']['id']
    limit = int(request.args.get('limit', 10))
    tasks = get_crawl_tasks(user_id, limit)
    return jsonify({'success': True, 'data': tasks})

@app.route('/api/stats')
@login_required
def api_stats():
    total = get_bidding_count()
    cached_urls = cache.get_url_count()
    return jsonify({
        'success': True,
        'data': {
            'total_records': total,
            'cached_urls': cached_urls,
            'regions_count': len(Config.REGIONS) - 1,
            'industries_count': len(Config.INDUSTRIES)
        }
    })

@app.route('/api/dedupe-test', methods=['POST'])
@login_required
def api_dedupe_test():
    data = request.get_json()
    test_title = data.get('title', '测试重复标题')
    test_url = data.get('url', 'http://test.com/duplicate')
    first_insert = insert_bidding({
        'title': test_title,
        'content': '测试内容',
        'url': test_url,
        'region': 'beijing',
        'industry': 'it',
        'publish_date': '2024-01-01',
        'source': '测试来源',
        'budget': 100,
        'keywords': '测试'
    })
    second_insert = insert_bidding({
        'title': test_title,
        'content': '测试内容',
        'url': test_url,
        'region': 'beijing',
        'industry': 'it',
        'publish_date': '2024-01-01',
        'source': '测试来源',
        'budget': 100,
        'keywords': '测试'
    })
    url_check = cache.is_url_duplicate(test_url)
    return jsonify({
        'success': True,
        'first_insert': first_insert,
        'second_insert': second_insert,
        'url_cached': url_check,
        'message': '去重功能验证完成'
    })

@app.route('/api/parse-test', methods=['POST'])
@login_required
def api_parse_test():
    data = request.get_json()
    html = data.get('html', '')
    if not html:
        html = '''
        <table>
            <tr><th>标题</th><th>发布日期</th></tr>
            <tr><td class="td_1"><a href="/bid/1">关于软件开发项目的招标公告</a></td><td>2024-01-15</td></tr>
            <tr><td>信息系统集成项目采购</td><td>2024-01-16</td></tr>
            <tr><td class="td_1">云计算平台建设招标</td><td>2024-01-17</td></tr>
        </table>
        '''
    results = crawler.parse_html(html)
    robust_results = crawler.test_parse_with_missing_tag(html)
    return jsonify({
        'success': True,
        'standard_parse': results,
        'robust_parse': robust_results,
        'message': f'标准解析找到{len(results)}条，容错解析找到{len(robust_results)}条'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
