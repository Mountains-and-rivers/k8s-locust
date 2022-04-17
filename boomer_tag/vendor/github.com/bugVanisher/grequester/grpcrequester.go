package grequester

import (
	"context"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/silenceper/pool"
	"google.golang.org/grpc"
)

// Requester ...
type Requester struct {
	addr      string
	service   string
	method    string
	timeoutMs uint
	pool      pool.Pool
}

// NewRequester ...
func NewRequester(addr string, service string, method string, timeoutMs uint, poolsize int) *Requester {
	//factory 创建连接的方法
	factory := func() (interface{}, error) { return grpc.Dial(addr, grpc.WithInsecure()) }

	//close 关闭连接的方法
	closef := func(v interface{}) error { return v.(*grpc.ClientConn).Close() }

	//创建一个连接池： 初始化5,最大连接200,最大空闲10
	poolConfig := &pool.Config{
		InitialCap: 5,
		MaxCap:     poolsize,
		MaxIdle:    10,
		Factory:    factory,
		Close:      closef,
		//连接最大空闲时间，超过该时间的连接 将会关闭，可避免空闲时连接EOF，自动失效的问题
		IdleTimeout: 15 * time.Second,
	}
	apool, _ := pool.NewChannelPool(poolConfig)
	return &Requester{addr: addr, service: service, method: method, timeoutMs: timeoutMs, pool: apool}
}

// getRealMethodName
func (r *Requester) getRealMethodName() string {
	return fmt.Sprintf("/%s/%s", r.service, r.method)
}

// Call 发起请求
func (r *Requester) Call(req interface{}, resp interface{}) error {
	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(r.timeoutMs)*time.Millisecond)
	defer cancel()
	cc, err := r.pool.Get()

	if err != nil {
		log.Printf("get rpc ClientConn error")
		return err
	}

	// 必须要把连接放回连接池否则一直创建新连接
	defer r.pool.Put(cc)

	if err = cc.(*grpc.ClientConn).Invoke(ctx, r.getRealMethodName(), req, resp, grpc.ForceCodec(&ProtoCodec{})); err != nil {
		fmt.Fprintf(os.Stderr, err.Error())
		return err
	}
	return nil
}
