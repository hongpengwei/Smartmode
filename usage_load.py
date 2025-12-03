import pyopencl as cl
import numpy as np
import time
import argparse
KERNEL_CODE = """
__kernel void burn(__global float *a) {
    int gid = get_global_id(0);
    float x = a[gid];
    for(int i = 0; i < 1000; i++) {
        x = x * 1.000001f + 0.000001f;
    }
    a[gid] = x;
}
"""

class IGPUAvgLoadSimulator:
    def __init__(self, target_load=0.3, arr_size=200_000, interval=1.0):
        self.target_load = max(0.0, min(1.0, target_load))
        self.arr_size = arr_size
        self.interval = interval

        # 找 Intel iGPU
        platforms = cl.get_platforms()
        self.igpu = None
        for p in platforms:
            if "Intel" in p.name:
                for d in p.get_devices():
                    if d.type & cl.device_type.GPU:
                        self.igpu = d
                        break
        if self.igpu is None:
            raise RuntimeError("找不到 Intel iGPU")

        print(f"使用 iGPU：{self.igpu.name}")

        # OpenCL context & queue
        self.ctx = cl.Context([self.igpu])
        self.queue = cl.CommandQueue(self.ctx)
        self.program = cl.Program(self.ctx, KERNEL_CODE).build()
        self.kernel = self.program.burn

        self.data = np.ones(self.arr_size, dtype=np.float32)
        self.buf = cl.Buffer(self.ctx, cl.mem_flags.READ_WRITE | cl.mem_flags.COPY_HOST_PTR, hostbuf=self.data)

    def set_load(self, new_load):
        self.target_load = max(0.0, min(1.0, new_load))
        print(f"已設定新平均負載: {int(self.target_load*100)}%")

    def run(self):
        print(f"開始 iGPU 模擬平均負載: {int(self.target_load*100)}%")
        print("Task Manager → GPU → Compute_0 顯示瞬時值，平均值由下方顯示")
        print("按 Ctrl+C 停止測試")

        try:
            while True:
                interval_start = time.time()
                compute_start = time.time()
                
                # full load 運算直到 compute_time 過完
                compute_time = self.interval * self.target_load
                while time.time() - compute_start < compute_time:
                    self.kernel(self.queue, (self.arr_size,), None, self.buf)
                    self.queue.finish()

                compute_end = time.time()
                actual_compute = compute_end - compute_start
                rest_time = self.interval - actual_compute

                # 休息
                if rest_time >= 0:
                    time.sleep(rest_time)

                interval_end = time.time()
                # 計算平均負載
                # avg_load = actual_compute / (interval_end - interval_start)
                # print(f"平均負載: {avg_load*100:.1f}%  (目標: {self.target_load*100:.0f}%)", end='\r')

        except KeyboardInterrupt:
            print("\n停止 iGPU 模擬平均負載")

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--load", type=float, default=0.5, help="0.0~1.0")
    args = parser.parse_args()
    simulator = IGPUAvgLoadSimulator(args.load)  # 初始平均負載 30%
    simulator.run()