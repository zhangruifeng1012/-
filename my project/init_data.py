import os
import random
from datetime import datetime, timedelta
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, insert_bidding, get_bidding_count
from config import Config

def generate_sample_data():
    regions = [r['id'] for r in Config.REGIONS if r['id'] != 'all']
    industries = [i['id'] for i in Config.INDUSTRIES]
    sources = [p['name'] for p in Config.DEFAULT_PAGES]
    
    titles_templates = {
        'it': ['软件开发服务项目', '信息系统集成招标', '云计算平台建设', '数据中心运维服务', '网络安全升级改造', '智能终端采购', '大数据分析平台', 'AI人工智能项目'],
        'construction': ['办公楼装修工程', '道路桥梁建设项目', '市政基础设施改造', '园林景观工程', '厂房建设项目', '商业综合体工程'],
        'medical': ['医疗设备采购项目', '医院信息化系统', '药品供应项目', '体检服务外包', '医疗器械招标', '智慧医院建设'],
        'education': ['教学设备采购', '在线教育平台建设', '培训服务外包', '教材教具供应', '实验室建设项目', '校园网升级改造'],
        'finance': ['审计服务项目', '财务咨询服务', '金融系统升级改造', '银行IT设备采购', '支付系统建设'],
        'energy': ['变电站建设项目', '智能电网改造升级', '光伏发电项目', '节能改造工程', '新能源充电桩建设', '电力设备采购'],
        'transport': ['公交车辆采购', '道路养护工程', '地铁设备维护', '智慧交通系统', '高速公路监控项目']
    }
    
    keywords_list = ['软件开发', '云计算', '大数据', '人工智能', '网络安全', '项目建设', '招标公告', 
                     '设备采购', '系统集成', '运维服务', '装修工程', '信息化', '智慧', '平台建设', '升级改造']
    
    print('正在生成示例数据...')
    count = 0
    
    for i in range(150):
        industry = random.choice(industries)
        template = random.choice(titles_templates.get(industry, ['项目招标']))
        region = random.choice(regions)
        days_ago = random.randint(0, 45)
        publish_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        title = f'关于{template}的招标公告（{Config.REGIONS[regions.index(region)]["name"]}）'
        keywords = random.sample(keywords_list, k=random.randint(2, 4))
        
        data = {
            'title': title,
            'content': f'本项目为{template}相关招标公告，项目位于{Config.REGIONS[regions.index(region)]["name"]}。详见招标文件要求及技术规范。',
            'url': f'http://example.com/bidding/{i}_{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'region': region,
            'industry': industry,
            'publish_date': publish_date,
            'source': random.choice(sources),
            'budget': round(random.uniform(50, 8000), 2),
            'keywords': ','.join(keywords)
        }
        
        if insert_bidding(data):
            count += 1
    
    print(f'✓ 成功生成 {count} 条示例招标数据')
    print(f'✓ 当前数据库总记录数: {get_bidding_count()}')
    return count

if __name__ == '__main__':
    init_db()
    generate_sample_data()
    print('\n数据生成完成！现在可以启动 app.py 查看系统')
