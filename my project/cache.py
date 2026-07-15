import json
import hashlib
import os
from datetime import datetime
from config import Config

class RedisCache:
    def __init__(self):
        self.cache_file = Config.CACHE_PATH
        self.data = {}
        self.url_set = set()
        self._load()
    
    def _load(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.data = data.get('cache', {})
                    self.url_set = set(data.get('urls', []))
            except:
                self.data = {}
                self.url_set = set()
    
    def _save(self):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'cache': self.data,
                    'urls': list(self.url_set)
                }, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def get(self, key):
        if key in self.data:
            item = self.data[key]
            if 'expire' in item:
                if datetime.now().strftime('%Y-%m-%d %H:%M:%S') > item['expire']:
                    del self.data[key]
                    return None
            return item.get('value')
        return None
    
    def set(self, key, value, ttl=3600):
        expire_time = datetime.fromtimestamp(datetime.now().timestamp() + ttl).strftime('%Y-%m-%d %H:%M:%S')
        self.data[key] = {'value': value, 'expire': expire_time}
        self._save()
    
    def sadd(self, key, member):
        if key not in self.data:
            self.data[key] = {'value': [], 'type': 'set'}
        if not isinstance(self.data[key]['value'], list):
            self.data[key] = {'value': [], 'type': 'set'}
        if member not in self.data[key]['value']:
            self.data[key]['value'].append(member)
            self._save()
            return True
        return False
    
    def smembers(self, key):
        if key in self.data and isinstance(self.data[key].get('value'), list):
            return self.data[key]['value']
        return []
    
    def sismember(self, key, member):
        return member in self.smembers(key)
    
    def is_url_duplicate(self, url):
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return url_hash in self.url_set
    
    def add_url(self, url):
        url_hash = hashlib.md5(url.encode()).hexdigest()
        if url_hash not in self.url_set:
            self.url_set.add(url_hash)
            self._save()
            return True
        return False
    
    def get_url_count(self):
        return len(self.url_set)

cache = RedisCache()
