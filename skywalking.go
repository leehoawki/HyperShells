package main

import (
	"context"
	_ "net/http"
	"time"

	// Use this for Elasticsearch 6.x:
	"github.com/olivere/elastic"
)

const DAYS = 7

func main() {
	client, err := elastic.NewClient(elastic.SetURL("http://192.168.1.109:9200"))

	if err != nil {
		// Handle error
		panic(err)
	}

	for _, v := range getIndices() {
		println(v)
	}

	getSum(client, "service_cpm_day-20191113")

	defer client.Stop()
}

func getIndices() []string {
	indices := make([]string, DAYS)
	for i := 0; i < DAYS; i++ {
		t := time.Now().AddDate(0, 0, -i)
		indices[i] = t.Format("service_cpm_day-20060102")
	}
	return indices
}

func getSum(client *elastic.Client, indices string) {
	println("query for data, index=" + indices)

	searchResult, err := client.
		Search().
		Index(indices).
		Query(elastic.NewMatchAllQuery()).
		Size(0).
		Pretty(true).
		Do(context.Background())

	if err != nil {
		panic(err)
	}

	println(searchResult)
}
