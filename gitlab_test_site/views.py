import re
from django.http import HttpResponse
from bs4 import BeautifulSoup
import requests
import configs

PERSONAL_TOKEN = configs.PERSONAL_TOKEN
PROJECTS_IDS = configs.PROJECTS_IDS
REPO_COMMON_URL = configs.REPO_COMMON_URL

def get_repos_info(projects_numbers_array=None):
    headers = {'PRIVATE-TOKEN': PERSONAL_TOKEN}
    temp_map = {}
    for i in projects_numbers_array:
        last_pipeline_info = \
            requests.get(f'{REPO_COMMON_URL}api/v4/projects/{i}/pipelines/', headers=headers).json()[0]
        id = i
        pipeline_url = last_pipeline_info['web_url']
        project_name = list(filter( lambda x: x!= '', last_pipeline_info['web_url'].split('-')[0].split('/')))[-1]
        status = last_pipeline_info['status']
        temp_map[str(id)] = {'project_name': str(project_name), 'status': str(status),
                             'pipeline_url': str(pipeline_url)}
    return temp_map


def get_right_alert(text_status):
    statuses = {
        'success': 'alert-success',
        'failed': 'alert-danger',
        'canceled': 'alert-warning',
        'running': 'alert-info',
        'pending': 'alert-primary',
        'skipped': 'alert-dark',
        'created': 'alert-light',
        'manual': 'alert-dark',
    }
    return statuses.get(text_status, 'alert-dark')


def get_right_image(text_status):
    statuses = {
        'passed': 'https://i.pinimg.com/originals/c4/27/7d/c4277d9d382493ff8c55e975d438ed1c.gif',  ## Задублировал??
        'success': 'https://i.pinimg.com/originals/c4/27/7d/c4277d9d382493ff8c55e975d438ed1c.gif',  ## Задублировал??
        'failed': 'https://media.tenor.com/images/c23d08a50e4984e77436795d6e353850/tenor.gif',
        'canceled': 'https://cdn.getstickerpack.com/storage/uploads/sticker-pack/pepe-the-frog/sticker_6.png?207ef57c8599e443acc1f0b0ff6723c4',
        'running': 'https://media.tenor.com/images/120bd0babbfc06a038fca08a516a8191/tenor.gif',
        'pending': 'http://img0.reactor.cc/pics/post/full/%D0%B3%D0%B8%D1%84%D0%BA%D0%B8-%D0%BF%D0%B5%D1%81%D0%BE%D1%87%D0%BD%D0%B8%D1%86%D0%B0-3659828.gif',
        'skipped': 'https://tenor.com/view/pepe-frog-gif-9987448',
        'created': 'https://w7.pngwing.com/pngs/552/807/png-transparent-pepe-frog-illustration-gif-imgur-tenor-know-your-meme-twitch-emotes-vertebrate-meme-fictional-character.png',
        'manual': 'https://tenor.com/view/pepe-frog-cave-gif-14781630',
    }
    return statuses.get(text_status, 'alert-dark')

def merge_2_dicts(d1, d2): ## Версия только для склеивания list !!!
    d1_keys = d1.keys()
    d2_keys = d2.keys()

    for cur_key in d1_keys:
        if cur_key in d2_keys:
            d2_previous = d2[cur_key]
            d2[cur_key] = { *d2_previous, *d1[cur_key]}

def get_last_pipeline_info(project_id):
    headers = {'PRIVATE-TOKEN': PERSONAL_TOKEN}

    get_last_pipeline_number = \
    requests.get(f'{REPO_COMMON_URL}api/v4/projects/{project_id}/pipelines/', headers=headers).json()[0]['id']
    get_last_pipelne_jobs_numbers = list(map(lambda x: x['id'], requests.get(
        f'{REPO_COMMON_URL}api/v4/projects/{project_id}/pipelines/{get_last_pipeline_number}/jobs',
        headers=headers).json()))


    res_spent_time = 0
    res_passed = 0
    res_skipped = 0
    res_failed = 0
    res_error = 0
    xfailed = 0
    xpassed = 0

    test_names_and_statuses = {}
    res_map = {}
    count = 0

    for cur_job_number in get_last_pipelne_jobs_numbers:
        try:
            html_report = requests.get(
                f'{REPO_COMMON_URL}api/v4/projects/{project_id}/jobs/{cur_job_number}/artifacts/report.html',
                headers=headers).text
            if html_report == '{"message":"404 Not Found"}':
                count += 1
                continue

            res_spent_time += int(
                re.findall('\d{1,5} tests ran in \d{1,5}.\d{1,5} seconds. ', html_report)[0].split('in')[1].split('.')[0])
            res_passed += int(re.findall('\d{1,5} passed', html_report)[0].split('passed')[0])
            res_skipped += int(re.findall('\d{1,5} skipped', html_report)[0].split('skipped')[0])
            res_failed += int(re.findall('\d{1,5} failed', html_report)[0].split('failed')[0])
            res_error += int(re.findall('\d{1,5} errors', html_report)[0].split('errors')[0])
            xfailed += int(re.findall('\d{1,5} expected failures', html_report)[0].split('expected')[0])
            xpassed += int(re.findall('\d{1,5} unexpected passes', html_report)[0].split('unexpected')[0])

            test_names_and_statuses_from_file = get_test_name_and_status(html_report)

            if test_names_and_statuses == {}:
                test_names_and_statuses.update(test_names_and_statuses_from_file)
            else:
                res_map = {}
                res_map.update(test_names_and_statuses)
                for key in test_names_and_statuses_from_file.keys():
                    old_values = res_map[key]
                    new_values = test_names_and_statuses_from_file[key]
                    res_map[key] = [*old_values, *new_values]
                test_names_and_statuses = res_map
        except: pass

        # test_names_and_statuses = {**test_names_and_statuses, **ss}

    res_map['res_spent_time'] = res_spent_time
    res_map['res_passed'] = res_passed
    res_map['res_skipped'] = res_skipped
    res_map['res_failed'] = res_failed
    res_map['res_error'] = res_error
    res_map['res_xfailed'] = xfailed
    res_map['res_xpassed'] = xpassed

    res_map['test_names_and_statuses'] = test_names_and_statuses
    if count == len(
            get_last_pipelne_jobs_numbers):  ## Если все время не мог считать report.html из всех job -- выставляем N/A -- нет данных
        for key in res_map.keys():
            res_map[key] = 'N/A'

    if test_names_and_statuses == {}:
        for key in res_map.keys():
            res_map[key] = 'N/A'

    return res_map


def make_list_of_tests(list):
    """ <a class="dropdown-item" href="#">Action</a>"""
    res_str = ''
    for _ in list:
        res_str += f'<a class="dropdown-item" href="#">{_}</a>'
    return str(res_str)

def make_pop_up_tests_list(tests_results,status,btn):
    return f"""
                            <li class="list-group-item">
                            <div class="btn-group">
                              <button type="button" class="btn btn-{btn} dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                                {status}:: {tests_results[f'res_{status}']}
                              </button>
                              <div class="dropdown-menu">
                                {make_list_of_tests(
                                    tests_results['test_names_and_statuses'][status] if tests_results['res_passed']  != 'N/A' else ''
                                )}
                              </div>
                            </div>
                        </li>
          """

def make_tests_procent_line(percent_of_good_tests,percent_of_failed_tests,
                            percent_of_skipped_tests,percent_of_others_tests):
    return f"""
                            <li class="list-group-item">
                            <div class="progress">
                                <div class="progress-bar bg-success" role="progressbar" style="width: {percent_of_good_tests * 100}%" aria-valuenow="30" aria-valuemin="0" aria-valuemax="100"></div>
                                <div class="progress-bar bg-danger" role="progressbar" style="width: {percent_of_failed_tests * 100}%" aria-valuenow="15" aria-valuemin="0" aria-valuemax="100"></div>
                                <div class="progress-bar bg-info" role="progressbar" style="width: {percent_of_skipped_tests * 100}%" aria-valuenow="15" aria-valuemin="0" aria-valuemax="100"></div>
                                <div class="progress-bar bg-warning" role="progressbar" style="width: {percent_of_others_tests * 100}%" aria-valuenow="15" aria-valuemin="0" aria-valuemax="100"></div>
                            </div>
                        </li>
                        """

def make_html(map):
    res_str = ''
    res_map = {}
    count = 0

    for key in map.keys():

        tests_results = get_last_pipeline_info(key)

        if tests_results['res_passed'] != 'N/A':
            all_tests = tests_results['res_passed'] + tests_results['res_failed'] \
                        + tests_results['res_skipped'] + tests_results['res_error'] \
                        + tests_results['res_xfailed'] + tests_results['res_xpassed']

            percent_of_good_tests = tests_results['res_passed'] / all_tests
            percent_of_failed_tests = tests_results['res_failed'] / all_tests
            percent_of_skipped_tests = tests_results['res_skipped'] / all_tests
            percent_of_others_tests = (tests_results['res_error'] + tests_results['res_xfailed'] +
                                       tests_results['res_xpassed']) / all_tests


        cur_block = f"""
                  <div class="card" style="width: 18rem;">
                      <img src="{get_right_image(map[key]['status'])}" class="card-img-top">
                      <div class="card-body">
                        <h5 class="card-title"> {map[key]['project_name']}</h5>
                      </div>
                      <ul class="list-group list-group-flush">
                        <li class="list-group-item">
                        <p>Статус последнего pipeline</p>
                        <p class="alert {get_right_alert(map[key]['status'])}" role="alert"> {map[key]['status']}</p>
                        </li>
                    
                        {
                        make_tests_procent_line(percent_of_good_tests,percent_of_failed_tests,
                                                percent_of_skipped_tests,percent_of_others_tests)
                        if tests_results['res_passed'] != 'N/A'
                        else ''}

                        {make_pop_up_tests_list(tests_results=tests_results, status='passed',  btn='success') if tests_results['res_passed'] != 'N/A' else ''}
                        {make_pop_up_tests_list(tests_results=tests_results, status='failed', btn='danger') if tests_results['res_passed'] != 'N/A' else ''}
                        {make_pop_up_tests_list(tests_results=tests_results, status='skipped', btn='info') if tests_results['res_passed'] != 'N/A' else ''}
                        {make_pop_up_tests_list(tests_results=tests_results, status='error', btn='warning') if tests_results['res_passed'] != 'N/A' else ''}
                        {make_pop_up_tests_list(tests_results=tests_results, status='xfailed', btn='warning') if tests_results['res_passed'] != 'N/A' else ''}
                        {make_pop_up_tests_list(tests_results=tests_results, status='xpassed', btn='warning') if tests_results['res_passed'] != 'N/A' else ''}
                      </ul>
                      <div class="card-body">
                        <a href="{map[key]['pipeline_url']}" class="card-link">Link to pipeline</a>
                        <br>
                      </div>
                  </div>
                """


        res_str += cur_block
        res_map[str(count)] = cur_block
        count += 1

    return res_map


def get_test_name_and_status(html):
    soup = BeautifulSoup(html, features="html.parser")
    temp_map = {}
    all_tests_res = list(map(lambda x: x.replace('<td class="col-result">', '').replace('td', ''),
                             list(map(lambda x: x.text, soup.find_all('td', class_="col-result")))))
    all_tests_names = list(map(lambda x: x.replace('<td class="col-name">', '').replace('td', ''),
                               list(map(lambda x: x.text, soup.find_all('td', class_="col-name")))))
    for _ in range(len(all_tests_names)): temp_map[all_tests_names[_]] = all_tests_res[_].lower()
    res_map = {
        'passed': [],
        'skipped': [],
        'failed': [],
        'error': [],
        'xfailed': [],
        'xpassed': [],
    }
    for cur_test in temp_map.keys():
        res_map[temp_map[cur_test]].append(cur_test)
    return res_map


def get_all_repos_map(projects_maps):
    res=''
    for cur_item in projects_maps:
        res += f"""
                  <li class="list-group-item">
                    {projects_maps[cur_item]}
                  </li>
                """
    return res

def index(request):

    try:
        temp_map = make_html(
            get_repos_info(PROJECTS_IDS))  ## Как-то красиво через цикл выводить
        html_text = f"""
            <!DOCTYPE html>
            <html>
                <head>
                    <title>Get Gitlab Autotests Results</title>
                    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/css/bootstrap.min.css" integrity="sha384-9aIt2nRpC12Uk9gS9baDl411NQApFmC26EwAOH8WgZl5MYYxFfc+NcPb1dKGj7Sk" crossorigin="anonymous">
                    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js" integrity="sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVy38MVBnE+IbbVYUew+OrCXaRkfj" crossorigin="anonymous"></script>
                    <script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.0/dist/umd/popper.min.js" integrity="sha384-Q6E9RHvbIyZFJoft+2mJbHaEWldlvI9IOYy5n3zV9zzTtmI3UksdQRVvoxMfooAo" crossorigin="anonymous"></script>
                    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/js/bootstrap.min.js" integrity="sha384-OgVRvuATP1z7JjHLkuOU7Xw704+h835Lr+6QL9UvYjZE3Ipu6Tp75j7Bh/kR0JKI" crossorigin="anonymous"></script>
                </head>
                <body>
                    <ul class="list-group list-group-horizontal">
                        {get_all_repos_map(temp_map)}
                    </ul>
                </body>
            </html>
        """
    except:
        html_text = f"""
              <!DOCTYPE html>
            <html>
                <head>
                    <title>Get Gitlab Autotests Results</title>
                    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/css/bootstrap.min.css" integrity="sha384-9aIt2nRpC12Uk9gS9baDl411NQApFmC26EwAOH8WgZl5MYYxFfc+NcPb1dKGj7Sk" crossorigin="anonymous">
                    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js" integrity="sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVy38MVBnE+IbbVYUew+OrCXaRkfj" crossorigin="anonymous"></script>
                    <script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.0/dist/umd/popper.min.js" integrity="sha384-Q6E9RHvbIyZFJoft+2mJbHaEWldlvI9IOYy5n3zV9zzTtmI3UksdQRVvoxMfooAo" crossorigin="anonymous"></script>
                    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/js/bootstrap.min.js" integrity="sha384-OgVRvuATP1z7JjHLkuOU7Xw704+h835Lr+6QL9UvYjZE3Ipu6Tp75j7Bh/kR0JKI" crossorigin="anonymous"></script>
                </head>
                <body>
                    <p align="center">Can't load page</p>
                </body>
            </html>
        """


    return HttpResponse(html_text)

    # return HttpResponse("Hello, world. You're at the polls index.")
