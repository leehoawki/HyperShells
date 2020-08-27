package main

import (
	"fmt"
	"runtime"
	"time"

	"github.com/shirou/gopsutil/cpu"
	"github.com/shirou/gopsutil/disk"
	"github.com/shirou/gopsutil/mem"
)

const (
	B  = 1
	KB = 1024 * B
	MB = 1024 * KB
	GB = 1024 * MB
)

func main() {
	DiskCheck()
	OSCheck()
	CPUCheck()
	RAMCheck()
}

//服务器硬盘使用量
func DiskCheck() {
	u, _ := disk.Usage("/")
	usedMB := int(u.Used) / MB
	usedGB := int(u.Used) / GB
	totalMB := int(u.Total) / MB
	totalGB := int(u.Total) / GB
	usedPercent := int(u.UsedPercent)
	fmt.Printf("Free space: %dMB (%dGB) / %dMB (%dGB) | Used: %d%%\n", usedMB, usedGB, totalMB, totalGB, usedPercent)
}

//OS
func OSCheck() {
	fmt.Printf("goOs:%s,compiler:%s,numCpu:%d,version:%s,numGoroutine:%d\n", runtime.GOOS, runtime.Compiler, runtime.NumCPU(), runtime.Version(), runtime.NumGoroutine())
}

//CPU 使用量
func CPUCheck() {
	cpus, err := cpu.Percent(time.Duration(200)*time.Millisecond, true)
	if err == nil {
		for i, c := range cpus {
			fmt.Printf("cpu%d : %f%%\n", i, c)
		}
	}
}

//内存使用量
func RAMCheck() {
	u, _ := mem.VirtualMemory()
	usedMB := int(u.Used) / MB
	totalMB := int(u.Total) / MB
	usedPercent := int(u.UsedPercent)
	fmt.Printf("usedMB:%d,totalMB:%d,usedPercent:%d", usedMB, totalMB, usedPercent)
}
