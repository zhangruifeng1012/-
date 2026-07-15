import os

class Config:
    SECRET_KEY = 'zhaobiao-secret-key-2024'
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    DB_PATH = os.path.join(DATA_DIR, 'bidding.db')
    CACHE_PATH = os.path.join(DATA_DIR, 'cache.json')
    
    CRAWLER_TIMEOUT = 30
    MAX_RETRIES = 3
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    
    DEFAULT_PAGES = [
        {'name': '中国政府采购网', 'url': 'http://www.ccgp.gov.cn/cggg/', 'type': 'gov'},
        {'name': '中国招标投标公共服务平台', 'url': 'http://www.cebpubservice.com/', 'type': 'bid'},
        {'name': '中国采购与招标网', 'url': 'https://www.chinabidding.cn/', 'type': 'bid'},
    ]
    
    REGIONS = [
        {'id': 'all', 'name': '全部'},
        {'id': 'beijing', 'name': '北京'},
        {'id': 'shanghai', 'name': '上海'},
        {'id': 'guangdong', 'name': '广东'},
        {'id': 'jiangsu', 'name': '江苏'},
        {'id': 'zhejiang', 'name': '浙江'},
        {'id': 'sichuan', 'name': '四川'},
        {'id': 'hubei', 'name': '湖北'},
        {'id': 'henan', 'name': '河南'},
        {'id': 'shandong', 'name': '山东'},
    ]
    
    INDUSTRIES = [
        {'id': 'it', 'name': '信息技术'},
        {'id': 'construction', 'name': '建筑工程'},
        {'id': 'medical', 'name': '医疗卫生'},
        {'id': 'education', 'name': '教育培训'},
        {'id': 'finance', 'name': '财政金融'},
        {'id': 'energy', 'name': '能源电力'},
        {'id': 'transport', 'name': '交通运输'},
    ]
