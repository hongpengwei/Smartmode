# import torch
# import argparse
# import time


# def allocate_vram(ratio, gpu_index=0):
#     if not torch.cuda.is_available():
#         print("No CUDA GPU detected.")
#         return None

#     device = torch.device(f"cuda:{gpu_index}")
#     props = torch.cuda.get_device_properties(device)

#     total_vram = props.total_memory
#     target_vram = int(total_vram * ratio)

#     print(f"Using GPU: {props.name}")
#     print(f"Total VRAM: {total_vram / (1024**2):.2f} MB")
#     print(f"Target allocation ({ratio*100:.1f}%): {target_vram / (1024**2):.2f} MB")

#     num_elements = target_vram // 4  # float32 = 4 bytes

#     try:
#         tensor = torch.zeros(num_elements, dtype=torch.float32, device=device)
#         print("Successfully allocated VRAM.")
#         return tensor
#     except RuntimeError as e:
#         print("Allocation failed:", e)
#         return None


# def main():
#     parser = argparse.ArgumentParser(description="Occupy a percentage of GPU VRAM.")
#     parser.add_argument("--ratio", type=float, default=0.5,
#                         help="Percentage of VRAM to occupy (0.0 - 1.0). Default = 0.5")
#     parser.add_argument("--gpu", type=int, default=0,
#                         help="GPU index to use. Default = 0")
    
#     args = parser.parse_args()

#     ratio = max(0.0, min(args.ratio, 1.0))  # 確保在 0~1 之間
#     tensor = allocate_vram(ratio, args.gpu)

#     if tensor is None:
#         print("Cannot allocate VRAM.")
#         return

#     print("Holding VRAM... Press Ctrl+C to exit.")
#     try:
#         while True:
#             time.sleep(5)
#     except KeyboardInterrupt:
#         print("Exiting. VRAM will be released.")


# if __name__ == "__main__":
#     main()
import torch
import time
import argparse

class GPUStressTester:
    def __init__(self, gpu_index=0, vram_ratio=0.5, target_load=0.5, interval=0.1, mat_size=1024):
        self.device = torch.device(f"cuda:{gpu_index}")
        self.vram_ratio = max(0.0, min(vram_ratio, 1.0))
        self.target_load = max(0.0, min(target_load, 1.0))
        self.interval = interval
        self.mat_size = mat_size
        self.tensor = None

    def allocate_vram(self):
        """占用指定比例 VRAM"""
        props = torch.cuda.get_device_properties(self.device)
        total_vram = props.total_memory
        target_vram = int(total_vram * self.vram_ratio)
        num_elements = target_vram // 4  # float32 = 4 bytes

        try:
            self.tensor = torch.zeros(num_elements, dtype=torch.float32, device=self.device)
            print(f"已成功占用 {self.vram_ratio*100:.1f}% VRAM (~{target_vram/1024**2:.1f} MB)")
        except RuntimeError as e:
            print("VRAM 分配失敗:", e)
            self.tensor = None

    def kernel(self):
        """單次運算 kernel，用於 GPU 負載"""
        a = torch.randn((self.mat_size, self.mat_size), device=self.device)
        b = torch.randn((self.mat_size, self.mat_size), device=self.device)
        c = torch.matmul(a, b)
        torch.cuda.synchronize()

    def run(self):
        if self.vram_ratio > 0:
            self.allocate_vram()

        print(f"開始 GPU 模擬平均負載: {self.target_load*100:.1f}%")
        print("按 Ctrl+C 停止測試")

        try:
            while True:
                interval_start = time.time()
                compute_start = time.time()

                compute_time = self.interval * self.target_load
                while time.time() - compute_start < compute_time:
                    self.kernel()

                compute_end = time.time()
                actual_compute = compute_end - compute_start
                rest_time = self.interval - actual_compute

                if rest_time > 0:
                    time.sleep(rest_time)

                interval_end = time.time()
                avg_load = actual_compute / (interval_end - interval_start)
                print(f"平均負載: {avg_load*100:.1f}% (目標: {self.target_load*100:.0f}%)", end='\r')

        except KeyboardInterrupt:
            print("\n測試停止。GPU 資源釋放中...")


def main():
    parser = argparse.ArgumentParser(description="GPU 壓力測試工具 (VRAM + Compute Load)")
    parser.add_argument("--gpu", type=int, default=0, help="GPU 編號")
    parser.add_argument("--vram", type=float, default=0.65, help="目標 VRAM 使用比例 (0~1)")
    parser.add_argument("--load", type=float, default=0.3, help="目標 GPU 平均負載 (0~1)")
    parser.add_argument("--interval", type=float, default=0.1, help="控制週期 (秒)")
    parser.add_argument("--mat", type=int, default=1024, help="矩陣大小 (影響負載強度)")

    args = parser.parse_args()

    tester = GPUStressTester(
        gpu_index=args.gpu,
        vram_ratio=args.vram,
        target_load=args.load,
        interval=args.interval,
        mat_size=args.mat
    )
    tester.run()


if __name__ == "__main__":
    main()


