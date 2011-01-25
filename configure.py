# -*- coding: utf-8 -*-

# configuration
base_url = 'http://kinozal.tv'
login_url = 'http://kinozal.tv/takelogin.php'
search_url = 'http://kinozal.tv/browse.php'

username = ''
password = ''

# Путь, по которому будут сохраняться файлы
base_path = './'
# Пример запроса, заполненный значениями по-умолчанию
# s - Текст запроса
# c - Раздел
# v - Формат
# y - Год
# t - Тип раздачи
# a, o - Параметры сортировки
# Допустимые значения не привожу, ибо лень
base_query = {'s': '', 'c': '0', 'v': '0', 'y': '', 't': '0', 'a': '0', 'o': '0'}
# Запросы для выполнения
# Первый параметр - имя файла, второй - заголовок фида, третий - описание фида,
# четвёртый - запрос
tasks = [
         ('futurama', 'Futurama on Kinozal.tv', '', 
          {'s': 'futurama', 'c': '0', 'v': '0', 'y': '', 't': '0', 'a': '0', 'o': '0'}),
         ('simpsons', 'Simpsons on Kinozal.tv', '', 
          {'s': 'simpsons', 'c': '0', 'v': '0', 'y': '', 't': '0', 'a': '0', 'o': '0'}),
         ('house', 'House MD on Kinozal.tv', '', 
          {'s': 'доктор хаус', 'c': '0', 'v': '0', 'y': '', 't': '0', 'a': '0', 'o': '0'}),
         ('tbb', 'Theory of Big Bang on Kinozal.tv', '', 
          {'s': 'теория большого взрыва', 'c': '0', 'v': '0', 'y': '', 't': '0', 'a': '0', 'o': '0'})
         ]