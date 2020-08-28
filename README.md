### Описание ::
!!!Только для Gitlab!!!

Простой сайт написанный на Django(прямо кустарно), позволяющий в Gitlab ::
1. Либо просто посмотреть состония последних прогонок pipeline.
2. Если в пайплайнах есть артефакты созданные с помощью библиотеки `pytest-html`(https://pypi.org/project/pytest-html/),
  тогда дополнительно покажет процентное соотнощение тестов + разобьет тесты по категориям, которые
  указаны в `pytest-html` --
<br>
  `passed`
<br>
  `skipped`
<br>
  `failed`
<br>
  `error`
<br>
  `xfailed`
<br>
  `xpassed`
<br>


### Как запускать ::
В файле configs.py(в корневой папке) нужно заполнить 4 поля -
<br>
`PERSONAL_TOKEN = ''` // Если нужен = Personal_Token Gitlab - создается в самом gitlab в разделе профиль юзера. Можно оставить пустым.
Создается здесь - https://gitlab.com/profile/personal_access_tokens. 
<br>
`PROJECTS_IDS = []` // Номера проектов . Пример :: ['1','2','3']
<br>
`REPO_COMMON_URL = ''` // Основная URL к гитлабу . Пример :: https://github.com/
<br>
`ALLOWED_HOSTS = []` // Доступ разрешенных ip - настройки Django, по которым будем обращаться к сайту.
Т.е. если хотим запускать сайт локально - заполняем ['localhost'] - и сможем видеть сайт по пути localhost:<номер порта>
или ['1.2.3.4'] - и тогда сможем открыть по пути 1.2.3.4:<номер порта>. Второй вариант нужен , если
мы хотим "расшарить сайт в интернет".(Поделиться с коллегами).
<br>


### Пример запуска ::
Заполняем файл configs.py следующим образом 
<br>
PERSONAL_TOKEN = '<Ваше personal_token >'
<br>
PROJECTS_IDS = ['19127825','18327953']
<br>
REPO_COMMON_URL = 'https://gitlab.com/'
<br>
ALLOWED_HOSTS = ['localhost']
<br>

И в проекте , в корневой папке в консоли пишем ::
python manage.py runserver localhost:8888
(python может быть python3 или может и без него команда запустится, 
т.е. надо будет ввести - manage.py runserver localhost:8888)
И после запуска сервера, он будет доступен нам по адресу -- http://localhost:8888/

![](https://github.com/s191k/pytest_pepe_html_report/raw/master/example_pepe.png)

### TODO ::
1. Сделать как библиотеку? (С созданием главного из которого будет запускаться django-сервер)
2. Сделать контейнер который будет подниматься по пути localhost/ ip ? 
