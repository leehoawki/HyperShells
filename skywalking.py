from elasticsearch import Elasticsearch
import datetime
import time

DAYS = 5


def getIndices():
    indices = []
    begin_date = (datetime.datetime.now() - datetime.timedelta(days=DAYS)).strftime("%Y%m%d")
    begin_date = datetime.datetime.strptime(begin_date, "%Y%m%d")
    end_date = datetime.datetime.strptime(time.strftime('%Y%m%d', time.localtime(time.time())), "%Y%m%d")
    while begin_date < end_date:
        date_str = begin_date.strftime("%Y%m%d")
        indices.append(date_str)
        begin_date += datetime.timedelta(days=1)
    return indices


def getCpm(client, indice):
    response = client.search(
        index=indice,
        body={
            "query": {
                "match_all": {

                }
            },
            "aggs": {
                "x": {"sum": {"field": "total"}}
            }
        })
    return str(int(response['aggregations']['x']['value']))


if __name__ == '__main__':
    client = Elasticsearch(hosts=["http://10.65.3.34:19200/"])
    for i in getIndices():
        print(i + ":" + getCpm(client, "cloud-monitor_service_cpm_hour-" + i))
