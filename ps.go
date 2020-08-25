package main

import (
	"fmt"
	"github.com/akamensky/argparse"
	"github.com/wonderivan/logger"
	"net"
	"os"
	"strconv"
	"sync"
	"time"
)

func main() {
	logger.SetLogger(`{
  "Console": {
    "level": "ERROR"
  },
  "File": {
    "level": "INFO",
    "filename": "a.log",
    "permit": "0660"
  }
}`)
	parser := argparse.NewParser("sports", "Scan ports...")
	ip := parser.String("i", "ip", &argparse.Options{Required: true, Default: "127.0.0.1", Help: "IP"})
	err := parser.Parse(os.Args)
	if err != nil {
		fmt.Print(parser.Usage(err))
		return
	}

	scanIP := ScanIp{timeout: 10}
	scanIP.GetIpOpenPort(*ip)
}

type ScanIp struct {
	timeout int
	process int
}

func (s *ScanIp) GetIpOpenPort(ip string) {
	ports := s.getAllPorts()
	var wg sync.WaitGroup
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(seed int) {
			defer wg.Done()
			for _, v := range ports {
				if v%10 != seed {
					continue
				}
				opened := s.isOpen(ip, v)
				if opened {
					println(ip + ":" + strconv.Itoa(v))
				}
			}
		}(i)
	}
	wg.Wait()
}

func (s *ScanIp) getAllPorts() []int {
	ports := make([]int, 65536)
	for i := 0; i < 65536; i++ {
		ports[i] = i + 1
	}
	return ports
}

func (s *ScanIp) isOpen(ip string, port int) bool {
	conn, err := net.DialTimeout("tcp", fmt.Sprintf("%s:%d", ip, port), time.Millisecond*time.Duration(s.timeout))
	if err != nil {
		logger.Info(err.Error())
		return false
	}
	_ = conn.Close()
	return true
}
