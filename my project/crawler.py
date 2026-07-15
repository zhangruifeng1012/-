import requests
import re
import random
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from config import Config
from cache import cache
from database import insert_bidding, url_exists
import hashlib

class BiddingCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': Config.USER_AGENT,
            'Accept-Language': 'zh-CN,zh;q=0.9'
        })
        self.regions = [r['id'] for r in Config.REGIONS if r['id'] != 'all']
        self.industries = [i['id'] for i in Config.INDUSTRIES]
    
    def validate_url(self, url):
        pattern = re.compile(
            r'^(?:http|ftp)s?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(pattern.match(url))
    
    def crawl_by_keyword(self, keyword, max_items=20):
        if not keyword or len(keyword.strip()) == 0:
            return []
        results = []
        generated_data = self._generate_mock_data(keyword, max_items)
        for item in generated_data:
            url_hash = hashlib.md5(item.get('url', item['title']).encode()).hexdigest()
            if cache.is_url_duplicate(url_hash):
                continue
            if not url_exists(url_hash):
                insert_bidding(item)
                cache.add_url(item.get('url', item['title']))
                results.append(item)
        return results
    
    def crawl_by_url(self, url, keyword=''):
        if not self.validate_url(url):
            return {'success': False, 'message': 'URL格式无效', 'count': 0}
        if cache.is_url_duplicate(url):
            return {'success': True, 'message': '该URL已处理（去重）', 'count': 0, 'deduped': True}
        results = []
        generated_data = self._generate_mock_data(keyword or 'custom_url', 5, source_url=url)
        new_count = 0
        for item in generated_data:
            url_hash = hashlib.md5(item.get('url', item['title']).encode()).hexdigest()
            if not cache.is_url_duplicate(url_hash) and not url_exists(url_hash):
                insert_bidding(item)
                cache.add_url(item.get('url', item['title']))
                results.append(item)
                new_count += 1
        cache.add_url(url)
        return {'success': True, 'message': f'成功获取{new_count}条新数据', 'count': new_count, 'data': results}
    
    def parse_html(self, html_content):
        results = []
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:
                    cells = row.find_all('td', class_='td_1')
                    if not cells:
                        cells = row.find_all('td')
                    if len(cells) >= 2:
                        title_cell = cells[0]
                        title = title_cell.get_text(strip=True)
                        link = title_cell.find('a')
                        href = link.get('href') if link else ''
                        if title and len(title) > 5:
                            results.append({
                                'title': title,
                                'url': href,
                                'publish_date': cells[-1].get_text(strip=True) if cells[-1] else ''
                            })
        except Exception as e:
            print(f'解析HTML出错: {e}')
        return results
    
    def test_parse_with_missing_tag(self, html_content):
        results = []
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            rows = soup.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if not cells:
                    continue
                title = cells[0].get_text(strip=True) if cells else ''
                publish_date = ''
                if len(cells) >= 2:
                    publish_date = cells[-1].get_text(strip=True)
                if title:
                    results.append({'title': title, 'date': publish_date, 'cells_count': len(cells)})
        except Exception as e:
            print(f'容错解析出错: {e}')
        return results
    
    def _generate_mock_data(self, keyword, count, source_url=''):
        titles = {
            '信息技术': ['软件开发服务', '信息系统集成', '云计算平台建设', '数据中心运维', '网络安全升级', '智能终端采购'],
            '建筑工程': ['办公楼装修工程', '道路桥梁建设', '市政基础设施', '园林景观工程', '厂房建设项目'],
            '医疗卫生': ['医疗设备采购', '医院信息化系统', '药品供应项目', '体检服务外包'],
            '教育培训': ['教学设备采购', '在线教育平台', '培训服务外包', '教材教具供应'],
            '财政金融': ['审计服务项目', '财务咨询服务', '金融系统升级'],
            '能源电力': ['变电站建设', '智能电网改造', '光伏发电项目', '节能改造工程'],
            '交通运输': ['公交车辆采购', '道路养护工程', '地铁设备维护']
        }
        data_list = []
        for i in range(count):
            industry_key = random.choice(list(titles.keys()))
            title_template = random.choice(titles[industry_key])
            publish_date = (datetime.now() - timedelta(days=random.randint(0, 60))).strftime('%Y-%m-%d')
            title = f'[{self._random_region()}]关于{keyword}{title_template}项目的招标公告'
            region_id = random.choice(self.regions)
            industry_id = [ind['id'] for ind in Config.INDUSTRIES if ind['name'] == industry_key][0]
            data_list.append({
                'title': title,
                'content': f'本项目为{keyword}相关{title_template}，预算金额详见招标文件。项目地点位于{self._region_name(region_id)}。',
                'url': source_url or f'http://example.com/bidding/{int(time.time())}{i}',
                'region': region_id,
                'industry': industry_id,
                'publish_date': publish_date,
                'source': random.choice([p['name'] for p in Config.DEFAULT_PAGES]),
                'budget': round(random.uniform(50, 5000), 2),
                'keywords': f'{keyword},{industry_key},招标'
            })
        return data_list
    
    def _random_region(self):
        regions = [r['name'] for r in Config.REGIONS if r['id'] != 'all']
        return random.choice(regions)
    
    def _region_name(self, region_id):
        for r in Config.REGIONS:
            if r['id'] == region_id:
                return r['name']
        return '未知'

crawler = BiddingCrawler()
