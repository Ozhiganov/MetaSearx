'''
searx is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

searx is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with searx. If not, see < http://www.gnu.org/licenses/ >.

(C) 2015- by Alexandre Flament, <alex@al-f.net>
'''

from operator import itemgetter
from flask.ext.babel import gettext
from searx.engines import engines
import searx.metrology as metrology


def initialize():
    # initialize metrology
    # response time of a search (everything)
    metrology.configure_measure(0.1, 30, 'search', 'time')
    # response time of a search, without rendering
    metrology.configure_measure(0.1, 30, 'search', 'time', 'search')
    # response time of a search, only rendering
    metrology.configure_measure(0.1, 30, 'search', 'time', 'render')
    for engine in engines:
        # search count
        metrology.reset_counter(engine, 'search', 'count')
        # result count per requests
        metrology.configure_measure(1, 100, engine, 'result', 'count')
        # time for calling the "request" function
        metrology.configure_measure(0.1, 30, engine, 'time', 'request')
        # time for the HTTP(S) request
        metrology.configure_measure(0.1, 30, engine, 'time', 'search')
        # time for calling the callback function "response"
        # call everytime, even if the callback hasn't really call
        # to keep the call count synchronize with <engine>, time, search
        metrology.configure_measure(0.1, 30, engine, 'time', 'callback')
        # time to append the results
        # call everytime, even if the callback hasn't really call
        # to keep the call count synchronize with <engine>, time, search
        metrology.configure_measure(0.1, 30, engine, 'time', 'append')
        # global time (request, search, callback, append)
        # call everytime, even if the callback hasn't really call
        # to keep the call count synchronize with <engine>, time, search
        metrology.configure_measure(0.1, 30, engine, 'time', 'total')
        # bandwidth usage (from searx to outside), update for each HTTP request
        # warning : not used
        metrology.configure_measure(1024, 300, engine, 'bandwidth', 'up')
        # bandwidth usage (from outside to searx), uddate for each HTTP request
        # warning : only the bytes from the main requests,
        # an engine can make several HTTP requests per user request
        metrology.configure_measure(1024, 300, engine, 'bandwidth', 'down')
        # score of the engine
        metrology.reset_counter(engine, 'score')
        # count the number of timeout
        metrology.reset_counter(engine, 'error', 'timeout')
        # count the number of requests lib errors
        metrology.reset_counter(engine, 'error', 'requests')
        # count the other errors
        metrology.reset_counter(engine, 'error', 'other')
        # global counter of errors
        metrology.reset_counter(engine, 'error')


def get_engines_stats():
    # TODO refactor
    pageloads = []
    results = []
    scores = []
    errors = []
    scores_per_result = []

    max_pageload = max_results = max_score = max_errors = max_score_per_result = 0  # noqa

    for engine in engines.values():
        error_count = metrology.counter(engine.name, 'error')
        if error_count > 0:
            max_errors = max(max_errors, error_count)
            errors.append({'avg': error_count, 'name': engine.name})

    for engine in engines.values():
        m_result_count = metrology.measure(engine.name, 'result', 'count')
        if m_result_count.get_count() == 0:
            continue
        m_time_total = metrology.measure(engine.name, 'time', 'total')
        score_count = metrology.counter(engine.name, 'score')

        result_count_avg = m_result_count.get_average()
        search_count = metrology.counter(engine.name, 'search', 'count')
        time_total_avg = m_time_total.get_average()  # noqa
        if search_count > 0 and result_count_avg > 0:
            score = score_count / float(search_count)  # noqa
            score_per_result = score / result_count_avg
        else:
            score = score_per_result = 0.0
        max_results = max(result_count_avg, max_results)
        max_pageload = max(time_total_avg, max_pageload)
        max_score = max(score, max_score)
        max_score_per_result = max(score_per_result, max_score_per_result)
        pageloads.append({'avg': time_total_avg, 'name': engine.name})
        results.append({'avg': result_count_avg, 'name': engine.name})
        scores.append({'avg': score, 'name': engine.name})
        scores_per_result.append({
            'avg': score_per_result,
            'name': engine.name
        })

    for engine in pageloads:
        if max_pageload:
            engine['percentage'] = int(engine['avg'] / max_pageload * 100)
        else:
            engine['percentage'] = 0

    for engine in results:
        if max_results:
            engine['percentage'] = int(engine['avg'] / max_results * 100)
        else:
            engine['percentage'] = 0

    for engine in scores:
        if max_score:
            engine['percentage'] = int(engine['avg'] / max_score * 100)
        else:
            engine['percentage'] = 0

    for engine in scores_per_result:
        if max_score_per_result:
            engine['percentage'] = int(engine['avg']
                                       / max_score_per_result * 100)
        else:
            engine['percentage'] = 0

    for engine in errors:
        if max_errors:
            engine['percentage'] = int(float(engine['avg']) / max_errors * 100)
        else:
            engine['percentage'] = 0

    return [
        (
            gettext('Page loads (sec)'),
            sorted(pageloads, key=itemgetter('avg'))
        ),
        (
            gettext('Number of results'),
            sorted(results, key=itemgetter('avg'), reverse=True)
        ),
        (
            gettext('Scores'),
            sorted(scores, key=itemgetter('avg'), reverse=True)
        ),
        (
            gettext('Scores per result'),
            sorted(scores_per_result, key=itemgetter('avg'), reverse=True)
        ),
        (
            gettext('Errors'),
            sorted(errors, key=itemgetter('avg'), reverse=True)
        ),
    ]

def get_engines_stats2():
    stats = []
    max_error = max_score_per_result = 0  # noqa

    for engine in engines.values():
        engine_name = engine.name

        m_result_count = metrology.measure(engine.name, 'result', 'count')
        score_count = metrology.counter(engine.name, 'score')

        result_count_avg = m_result_count.get_average()
        search_count = metrology.counter(engine.name, 'search', 'count')
        if search_count > 0 and result_count_avg > 0:
            score = score_count / float(search_count)  # noqa
            score_per_result = score / result_count_avg
        else:
            score = score_per_result = 0.0

        stat = {
            'name': engine_name,
            'time_request': metrology.measure(engine_name, 'time', 'request').get_average(),  # noqa
            'time_search': metrology.measure(engine_name, 'time', 'search').get_average(),  # noqa
            'time_callback': metrology.measure(engine_name, 'time', 'callback').get_average(),  # noqa
            'time_total': metrology.measure(engine_name, 'time', 'total').get_average(),  # noqa
            'result_count': m_result_count.get_sum(),
            'search_count': search_count,
            'error_count': int(metrology.counter(engine_name, 'error')),
            'error_timeout_count': int(metrology.counter(engine_name, 'error', 'timeout')),
            'error_requests_count': int(metrology.counter(engine_name, 'error', 'requests')),
            'score': score,
            'score_per_result': score_per_result
            }

        stat['time_total'] = stat['time_request'] + stat['time_search'] + stat['time_callback']
        stat['time_total_detail'] = metrology.measure(engine_name, 'time', 'total').get_qp()
        stat['error_other_count'] = stat['error_count'] - stat['error_requests_count'] - stat['error_timeout_count']

        max_error = max(max_error, stat['error_count'])
        max_score_per_result = max(max_score_per_result, stat['score_per_result'])

        if search_count or stat['error_count'] > 0:
            stats.append(stat)

    # time
    stats_time = sorted(stats, key=itemgetter('time_total'), reverse=True)
    stats_time_detail = {}
    for stat in stats:
        stats_time_detail[stat['name']] = stat['time_total_detail']

    # errors
    stats_error = []
    for stat in stats:
        if stat['error_count'] > 0:
            stats_error.append(stat)
    stats_error = sorted(stats_error, key=lambda e: int(e.get('error_count') * 100 / e.get('search_count')))

    # score
    stats_score = []
    max_score_per_result = 0
    for stat in stats:
        max_score_per_result = max(max_score_per_result, stat["score_per_result"])
        stats_score.append([stat["result_count"], stat["score_per_result"], stat["time_total"],
                           stat["name"], stat["score"]])

    stats_score = sorted(stats_score, key=lambda x: x[4], reverse=True)

    if max_score_per_result > 0:
        score_step = max_score_per_result / 400 * 20
    else:
        score_step = 1

    def shift_y(stat, offset, avoid):
        y = stat[1]
        for s in stats_score:
            if s[1] >= y and s != avoid:
                s[1] += offset

    # buble chart : make it readable by avoiding collision between bubles
    # implementation : no merge, x is never changed, only y is adjusted
    # when a collision is found, all (x,y) above are moved to keep the order
    # in other words, that's mean the absolute value y is meaningless,
    # but the order is preserved.
    # collision = nearby x distance < 4 and nearby y < score_step
    # x = result count, y = score per result
    for stat in stats_score:
        restart = True
        # safeguard : no more iteration than the (x,y) count
        maxIter = len(stats_score)
        # for each collision restart all tests, restart until nothing move
        while restart and maxIter > 0:
            restart = False
            maxIter -= 1
            # for each other (x,y), test collision
            # Warning : found only collision where stat is bellow s on y dimension
            for s in stats_score:
                if s != stat:
                    d1 = s[0] - stat[0]
                    d2 = s[1] - stat[1]
                    if (abs(d1) < 4) and d2 < score_step*2 and d2 >= 0:
                        # collision found (stat is above)
                        # move all (x,y) above stat to avoid collision
                        shift_y(s, score_step*3, stat)
                        # everything may has changed : restart
                        restart = True
                        break

    # return result
    return {
        'title': gettext('Engine stats'),
        'title_search_page': gettext('Search page'),
        'ticks_search_time': [float(x+1)/10 for x in range(0, len(metrology.measure('search', 'time').quartiles))],
        'search_time': {
            'labels': {
                'title': gettext('Total server time'),
                'xaxis': gettext('Time (sec)'),
                'yaxis': gettext('Percentage of requests')
                },
            'values': metrology.measure('search', 'time').get_qp(),
            'average': round(metrology.measure('search', 'time').get_average(), 3)
            },
        'time': {
            'labels': {
                'title': gettext('Page loads (sec)'),
                'xaxis': gettext('Page loads (sec)'),
                'serie_request': gettext('Preparation time (sec)'),
                'serie_search': gettext('Request time (sec)'),
                'serie_callback': gettext('Parsing time (sec)')
                },
            'engine': [e.get('name') for e in stats_time],
            'request': [e.get('time_request') for e in stats_time],
            'search': [e.get('time_search') for e in stats_time],
            'callback': [e.get('time_callback') for e in stats_time],
            'total': [e.get('time_total') for e in stats_time],
            'detail': stats_time_detail,
            'height': len(stats) * 1.6 + 5
            },
        'error': {
            'labels': {
                'title': gettext('Errors'),
                'xaxis': gettext('Error percentage'),
                'serie_other': gettext('Other errors'),
                'serie_requests': gettext('Requests errors'),
                'serie_timeout': gettext('Timeout errors')
                },
            'engine': [e.get('name') for e in stats_error],
            'other': [int(e.get('error_other_count') * 100 / e.get('search_count')) for e in stats_error],
            'requests': [int(e.get('error_requests_count') * 100 / e.get('search_count')) for e in stats_error],
            'timeout': [int(e.get('error_timeout_count') * 100 / e.get('search_count')) for e in stats_error],
            'height': len(stats_error)*1.6 + 5
            },
        'score': {
            'labels': {
                'title': gettext('Scores'),
                'xaxis': gettext('Number of results'),
                'yaxis': gettext('Scores per result')
                },
            'stat': stats_score
        },
        'count': len(stats)
        }

