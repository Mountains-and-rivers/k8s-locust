package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"time"

	"github.com/myzhan/boomer"
)

func getDemo() {
	start := time.Now()
	resp, err := http.Get("http://httpbin.org/get?name=Detector")

	if err != nil {
		log.Println(err)
		return
	}
	defer resp.Body.Close()
	fmt.Println(resp.Status)
	elapsed := time.Since(start)
	if resp.Status == "200 OK" {
		boomer.RecordSuccess("http", "sostreq", elapsed.Nanoseconds()/int64(time.Millisecond), int64(10))
	} else {
		boomer.RecordFailure("http", "sostreq", elapsed.Nanoseconds()/int64(time.Millisecond), "sostreq not equal")
	}
}

func postDemo() {
	start := time.Now()

	info := make(map[string]interface{})
	info["name"] = "Detector"
	info["age"] = 15
	info["loc"] = "深圳"
	// 将map解析未[]byte类型
	bytesData, _ := json.Marshal(info)
	// 将解析之后的数据转为*Reader类型
	reader := bytes.NewReader(bytesData)
	resp, _ := http.Post("http://httpbin.org/post",
		"application/json",
		reader)
	body, _ := ioutil.ReadAll(resp.Body)
	fmt.Println(string(body))
	elapsed := time.Since(start)
	if resp.Status == "200 OK" {
		boomer.RecordSuccess("http", "sostreq", elapsed.Nanoseconds()/int64(time.Millisecond), int64(10))
	} else {
		boomer.RecordFailure("http", "sostreq", elapsed.Nanoseconds()/int64(time.Millisecond), "sostreq not equal")
	}
}

func main() {
	task1 := &boomer.Task{
		Name: "sostreq",
		// The weight is used to distribute goroutines over multiple tasks.
		Weight: 20,
		Fn:     getDemo,
	}

	task2 := &boomer.Task{
		Name: "sostreq",
		// The weight is used to distribute goroutines over multiple tasks.
		Weight: 10,
		Fn:     postDemo,
	}
	boomer.Run(task1, task2)
}
