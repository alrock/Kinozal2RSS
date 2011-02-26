# -*- coding: utf-8 -*-

from BeautifulSoup import BeautifulSoup
import re
import urllib
import mechanize
import codecs
import os
import datetime
from configure import *

class GrabberException:
    def __init__(self, message):
        self.message = message
        
    def str(self):
        return self.message
        
def datetime_convert(s):
	#r'(?P<day>[0-9]{2}) (?P<month>[^ ]*) (?P<year>[0-9]{4}) в (?P<hour>[0-9]{2}):(?P<minutes>[0-9]{2})'
    #r'(?P<when>^сегодня|^завтра|^вчера) в (?P<hour>[0-9]{2}):(?P<minutes>[0-9]{2})'
    
    when = {'сегодня': 0, 'завтра': 1, 'вчера': -1}
    month = {'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 
             'июня': 6, 'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 
             'ноября': 11, 'декабря': 12}
    
    m1 = re.search(r'(?P<when>^сегодня|^завтра|^вчера) в (?P<hour>[0-9]{2}):(?P<minutes>[0-9]{2})', s.encode('utf-8'))
    m2 = re.search(r'(?P<day>[0-9]{2}) (?P<month>[^ ]*) (?P<year>[0-9]{4}) в (?P<hour>[0-9]{2}):(?P<minutes>[0-9]{2})', s.encode('utf-8'))
    
    current_time = datetime.datetime.now()
    
    if m1:
    	current_time = current_time.replace(hour=int(m1.group('hour')), minute=int(m1.group('minutes')))
    	current_time += datetime.timedelta(days=when[m1.group('when')])
    elif m2:
    	current_time = datetime.datetime(day=int(m2.group('day')), month=int(month[m2.group('month')]), year=int(m2.group('year')), 
    	                                 hour=int(m2.group('hour')), minute=int(m2.group('minutes')))
    	                                 
    return current_time

class Grabber:
    
    def __init__(self):
        self.cookies = None
        self.opener = None

    def __create_opener(self, cookies_file):
        try:
            file = open(cookies_file, 'a')
        except IOError as e:
            print e
            return None
        finally:
        	file.close()
        
        # Активируем обработку cookies
        self.cookies = mechanize.MozillaCookieJar(filename = cookies_file)
        self.opener = mechanize.build_opener(mechanize.HTTPCookieProcessor(self.cookies))
        # Пытаемся загрузить куки из файла
        try:
            self.cookies.revert()
        except (IOError, mechanize._clientcookie.LoadError) as e:
            print e
        return self.opener
    
        

    def grab(self, query):
        """
        Устанавливает соединение с кинозалом и вытягивает страницу поиска, соотв.
        переданному в query (копия base_query) запросу
        """
        if not self.opener and not self.__create_opener(os.path.join(cookies_path, 'cookies.txt')):
            raise GrabberException("Error 1. Can't create/open cookies file.")
        
       
        tmp = [( k, v.decode('utf-8').encode('1251') ) for k,v in query.items()]
        q = '?' + urllib.urlencode(tmp)
        
        resp = self.opener.open(search_url+q)
        data = resp.read()
        print >> open(query['s']+'.html', 'w'), data
        #resp = self.opener.open(login_url) 
        # Проверяем корректность кук (весьма извращенным способом)
        if not re.search(r'/browse\.php', data):
            # Я почти гарантирую что мы не залогинились
            print 'Take login again ...'
            self.opener.open(login_url, urllib.urlencode({'username': username, 
                                                     'password':password}))
            self.cookies.save()
            
            resp = self.opener.open(search_url+q)
            data = resp.read()
            if not re.search(r'/browse.php', data):
            	raise GrabberException("Error 2. Oh no! I'm a robot!")
        
        #tmp = [( k, v.decode('utf-8').encode('1251') ) for k,v in query.items()]
        #q = '?' + urllib.urlencode(tmp)
        
        #resp = self.opener.open(search_url+q)
        
        return data
        
    def _extract_text(self, tag):
        if tag.string: return [tag.string]
        result = []
        for i in tag.findAll(text = True):
            result.append(i.string)
        return result

    def parse(self, page):
        result = []
        soup = BeautifulSoup(page)
        # Задача: найти ссылку на описание раздачи, двинуться от неё вверх
        # по дереву документа до первого тега tr, далее для каждого td
        # извлекаем внутренний текст
        items = soup.findAll('a', {'href': re.compile(r'^/details.php')})
        
        for i in items:
            id = re.search(r'.*id=(?P<id>[0-9]+)', i['href'])
            torrent = {'id': id.group('id'),'link': base_url + i['href'], 
                       'name': ''.join(self._extract_text(i)).strip()}
            
            tr = i.findParent('tr')
            
            r = [''.join(self._extract_text(td)).strip() for td in tr.findAll(name = 'td', recursive = False)]

            torrent['time'] = datetime_convert(r[3]).strftime("%a, %d %b %Y %H:%M {0}").format('+0500')
            torrent['size'] = r[4]
            torrent['download'] = r[5]
            torrent['sid'] = r[6]
            torrent['pir'] = r[7]
            torrent['author'] = r[8]
     
            result.append(torrent)
            
        return result

    def to_rss(self, filename, title, desc, torrents):
        """
        Создает rss документ и возвращает в виде строки
        """
        items = []
        for t in torrents:
            items.append(u"""
                <item>
                    <title>{1}</title>
                    <link>{2}</link>
                    <description>
                        Торрент: {1} Добавлен: {3} Скачан: {4} Сидов: {5} Пиров: {6} Автор: {7}
                    </description>
                    <pubDate>{8}</pubDate>
                    <guid>{2}</guid>
                </item>
            """.format('', t['name'], t['link'], t['time'], t['download'], 
                       t['sid'], t['pir'], t['author'], t['time']))
            
        return u"""<?xml version="1.0"?>
            <rss version="2.0">
            <channel>
                <title>{0}</title>
                <link>http://alrock.ru/static/{1}.rss</link>
                <description>{2}</description>
                <language>ru-ru</language>
                <pubDate>{3}</pubDate>
                <generator>Python BeautifulSoup, Mechanize and hands 1.0</generator>
                <webMaster>alexandrsk@gmail.com</webMaster>
        """.format(title, filename, desc, 
                          datetime.datetime.now().strftime("%a, %d %b %Y %H:%M {0}").format('+0500')) + ''.join(items) + '</channel></rss>'

    def make_rss(self, filename, title, description, query):
        """
        Создаёт rss документ с заголовком title и описанием description, который
        соответствует поисковой выдаче запроса query. Результат записывается в
        файл filename
        """
        g = self.grab(query)
        torrents = self.parse(g)
        rss = self.to_rss(filename, title, description, torrents)
        
        file = codecs.open(filename+'.rss', 'w', 'utf-8')
        file.write(rss)
    
def accept_tasks():
    g = Grabber()
    for t in tasks:
        g.make_rss(os.path.join(base_path, t[0]), t[1], t[2], t[3])
    
if __name__ == '__main__':
    accept_tasks()
