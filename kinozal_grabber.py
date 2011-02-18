# -*- coding: utf-8 -*-

from BeautifulSoup import BeautifulSoup
import re
import urllib
import mechanize
import codecs
import os
from configure import *

class GrabberException:
    def __init__(self, message):
        self.message = message
        
    def str(self):
        return self.message

class Grabber:
    
    def __init__(self):
        self.coocies = None
        self.opener = None

    def __create_opener(self, cookies_file):
        try:
            file = open(cookies_file, 'w')
        except IOError as e:
            print e
            return None
        
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
        if not self.__create_opener(os.path.join(cookies_path, 'cookies.txt')):
            raise GrabberException("Error 1. Can't create/open cookies file.")
        
        # Проверяем корректность кук (весьма извращенным способом)
        resp = self.opener.open(login_url)
        if not re.search(r'/browse.php', resp.read()):
            # Я почти гарантирую что мы не залогинились
            print 'Take login again ...'
            self.opener.open(login_url, urllib.urlencode({'username': username, 
                                                     'password':password}))
            self.cookies.save()
        
        tmp = [( k, v.decode('utf-8').encode('1251') ) for k,v in query.items()]
        q = '?' + urllib.urlencode(tmp)
        
        resp = self.opener.open(search_url+q)
        
        return resp.read()
        
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
            
            iterator = 0
            for td in tr.findAll(name = 'td', recursive = False):
                text = ''.join(self._extract_text(td)).strip()
                if iterator == 3:
                    torrent['time'] = text
                elif iterator == 4:
                    torrent['size'] = text
                elif iterator == 5:
                    torrent['download'] = text
                elif iterator == 6:
                    torrent['sid'] = text
                elif iterator == 7:
                    torrent['pir'] = text
                elif iterator == 8:
                    torrent['author'] = text    
                iterator = iterator + 1
                
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
                <pubDate>Tue, 18 Jan 2011 22:00:00 GMT</pubDate>
                <generator>Python BeautifulSoup, Mechanize and hands 1.0</generator>
                <webMaster>alexandrsk@gmail.com</webMaster>
        """.format(title, filename, desc) + ''.join(items) + '</channel></rss>'

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