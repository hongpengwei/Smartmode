# Smart Mode - Intelligent Compute Device Selection System

A sophisticated system that intelligently selects the optimal AI model inference device (dGPU, iGPU, or NPU) based on real-time hardware utilization and system load.

## 📋 Overview

Smart Mode monitors your system's compute accelerators and automatically recommends the best device for running AI models, optimizing for throughput and latency based on current resource availability.

**Key Features:**
- 🖥️ Automatic hardware detection (dGPU, iGPU, NPU)
- 📊 Real-time GPU/NPU utilization monitoring
- 🎯 Intelligent device selection based on load thresholds
- 🔋 Battery health management (Windows)
- ⚡ OpenVINO model support with OVMS integration
- 🧪 Comprehensive benchmarking tools
- 🎮 Load simulation for testing

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Windows 10/11 or Linux
- NVIDIA GPU (optional, for dGPU support)
- Intel Arc/iGPU (optional)
- Intel Core Ultra with NPU (optional)

### Installation

1. **Create Virtual Environment**
```bash
python -m venv openvino_env
openvino_env\Scripts\activate  # Windows
source openvino_env/bin/activate  # Linux/macOS
```

2. **Install Dependencies**
```bash
pip install --upgrade pip
pip install openvino-genai==2025.3.0 wmi requests numpy psutil torch pyopencl fastmcp
```

3. **Download OVMS (OpenVINO Model Server)**
```bash
# Windows
curl -L https://github.com/openvinotoolkit/model_server/releases/download/v2025.3/ovms_windows_python_on.zip -o ovms.zip
tar -xf ovms.zip

# Linux - check official documentation
```

4. **Download Models**
```bash
# iGPU model
ovms.exe --pull --model_repository_path models \
  --source_model OpenVINO/Qwen3-8B-int4-ov --task text_generation

# NPU model
ovms.exe --pull --model_repository_path models \
  --source_model OpenVINO/Qwen3-8B-int4-cw-ov --task text_generation
```

---

## 📚 File Structure & Usage

### Core System Files

#### **[`main.py`](main.py)** - Main Intelligence Engine
Continuously monitors hardware and recommends optimal device selection.

```bash
python main.py
```

**Output Example:**
```
建議使用裝置: iGPU, 模型: OpenVINO/Qwen3-8B-int4-ov
建議使用裝置: NPU, 模型: OpenVINO/Qwen3-8B-int4-cw-ov
```

**Key Functions:**
- `get_igpu_npu_usage()` - Fetch current GPU/NPU utilization
- `pick_best_dgpu_model()` - Select dGPU model based on VRAM
- `select_best_device_and_model()` - Main selection logic

---

#### **[`detect_hw.py`](detect_hw.py)** - Hardware Detection
One-time hardware detection supporting Windows, Linux, macOS.

```bash
python detect_hw.py
```

**Output Example:**
```
🖥️ 獨立顯示卡 (dGPU): ✅ 偵測到
🎮 整合顯示卡 (iGPU): ✅ 偵測到
⚙️ 神經處理單元 (NPU): ✅ 偵測到
```

**Key Functions:**
- `detect_compute_devices()` - Detect all available accelerators
- `_detect_windows_gpu()` - Windows GPU detection via Registry
- `_detect_windows_npu()` - Windows NPU detection via PowerShell

---

#### **[`compute_info.py`](compute_info.py)** - Real-time GPU Monitoring
Fast GPU/NPU utilization monitoring using PowerShell Get-Counter.

```bash
python compute_info.py
```

**Output Example:**
```
🔹 iGPU   | 利用率:  45.23% | MEM:   512.30 MB
🔹 NPU    | 利用率:  12.50% | MEM:     0.00 MB
```

**Key Functions:**
- `get_gpu_utilization_fast()` - Get utilization in <100ms
- `luid_to_int()` - Convert LUID to integer for sorting
- `run_powershell()` - Execute PowerShell commands

---

#### **[`get_dgpu_usage.py`](get_dgpu_usage.py)** - NVIDIA GPU Monitoring
Monitor NVIDIA dGPU core utilization and VRAM using nvidia-smi.

```bash
python get_dgpu_usage.py
```

**Key Functions:**
- `get_dgpu_utilization_nvidia_smi()` - Returns GPU utilization (0-100%)
- `get_dgpu_vram()` - Returns available VRAM in GB
- `run_cmd()` - Execute shell commands

---

### Benchmarking & Testing

#### **[`benchmark_final.py`](benchmark_final.py)** - Automatic Threshold Detection
Find optimal iGPU/NPU switching point through automated testing.

```bash
python benchmark_final.py
```

**Key Functions:**
- `run_benchmark()` - Compare NPU vs iGPU throughput
- `auto_find_threshold()` - Automatically find switching point
- `benchmark_ovms()` - Test single model via OVMS REST API

**Output Example:**
```
⚡ Testing NPU...
⚡ Testing iGPU...

=== Result ===
NPU  (Qwen3-4B-int4-ov):  45.32 tok/s
iGPU (Qwen3-4B-int4-cw-ov): 38.12 tok/s
-------------------------------
🏆 NPU is faster

📌 建議切換點：CPU/iGPU load > 60% → 換 NPU
```

---

#### **[`benchmark_ovms.py`](benchmark_ovms.py)** - OVMS Performance Testing
Compare models across different devices via OVMS REST API.

```bash
python benchmark_ovms.py
```

**Requirements:**
- OVMS server running on port 8000 (iGPU) and 8001 (NPU)
- Models pre-loaded in OVMS

---

#### **[`final.py`](final.py)** - Complete Testing Pipeline
Integrated testing combining load simulation and benchmarking.

```bash
python final.py
```

**Workflow:**
1. Gradually increase iGPU load (30%-100%)
2. Benchmark NPU vs iGPU at each load level
3. Automatically detect switching threshold

---

### Load Simulation Tools

#### **[`usage_load.py`](usage_load.py)** - Intel iGPU Load Simulator
Simulate specified GPU load percentage using PyOpenCL.

```bash
python usage_load.py --load 0.5  # 50% load
```

**Parameters:**
- `--load`: Target load (0.0-1.0, default: 0.5)

**Key Class:**
- `IGPUAvgLoadSimulator` - Manages iGPU load simulation

---

#### **[`dgpu_usage.py`](dgpu_usage.py)** - NVIDIA GPU Stress Tester
Generate compute load and occupy VRAM on NVIDIA GPUs.

```bash
python dgpu_usage.py --gpu 0 --vram 0.65 --load 0.3
```

**Parameters:**
- `--gpu`: GPU index (default: 0)
- `--vram`: VRAM usage ratio (default: 0.65)
- `--load`: Average compute load (default: 0.3)
- `--interval`: Control cycle in seconds (default: 0.1)
- `--mat`: Matrix size affecting load intensity (default: 1024)

**Key Class:**
- `GPUStressTester` - GPU stress testing utility

---

### Battery Management

#### **[`battery_health.py`](battery_health.py)** - Battery Control
Enable/disable Windows battery health control mode (requires admin).

```bash
python battery_health.py
```

**Key Functions:**
- `set_battery_health()` - Apply battery health settings via WMI
- `is_admin()` - Check admin privileges
- `run_as_admin()` - Auto-elevate to admin if needed

---

#### **[`battery_health_mcp.py`](battery_health_mcp.py)** - MCP Server
Expose battery management as MCP (Model Context Protocol) tools.

```bash
python battery_health_mcp.py
# Server listens on http://localhost:8090/sse
```

**Available Tools:**
- `enable_battery_health()` - Enable battery health mode
- `disable_battery_health()` - Disable battery health mode

---

### Model Export & Conversion

#### **[`export_model.py`](export_model.py)** - OpenVINO Model Exporter
Convert and export models to OpenVINO format for OVMS deployment.

**Supported Tasks:**
- `text_generation` - LLM models
- `embeddings` - Embedding models
- `rerank` - Reranking models
- `image_generation` - Image generation models

**Example - Text Generation for NPU:**
```bash
python export_model.py text_generation \
  --source_model Qwen/Qwen3-4B \
  --target_device NPU \
  --config_file_path models/config.json \
  --model_repository_path models \
  --overwrite_models
```

**Key Functions:**
- `export_text_generation_model()` - Export LLM for text generation
- `export_embeddings_model()` - Export embedding models
- `add_servable_to_config()` - Register model in OVMS config

---

### Monitoring & Utilities

#### **[`compute_info_1.py`](compute_info_1.py)** - Continuous Monitoring
Infinite loop version of `compute_info.py` for persistent monitoring.

```bash
python compute_info_1.py  # Press Ctrl+C to stop
```

---

## 🔧 Configuration Files

### **[`config.json`](config.json)** - OVMS Model Configuration
Defines model names and paths for OVMS server.

```json
{
    "model_config_list": [
        { 
            "config": {
                "name": "Qwen3-8B-int4-cw-ov",
                "base_path": "C:\\path\\to\\models\\Qwen3-8B-int4-cw-ov"
            }
        }
    ]
}
```

---

### **[`config_mcp.json`](config_mcp.json)** - MCP Client Configuration
Points to local MCP server for battery management.

```json
{
  "mcpServers": {
    "battery_health": {
      "type": "sse",
      "url": "http://localhost:8090/sse"
    }
  }
}
```

---

## 📖 Documentation

### **[`README_v3.md`](README_v3.md)** - Complete Setup Guide
Comprehensive installation and configuration guide covering:
- OpenVINO GenAI installation
- OVMS download and setup
- Model download and conversion
- NPU acceleration setup
- OpenWebUI integration

### **[`REAMME_v2.md.txt`](REAMME_v2.md.txt)** - Legacy Setup Guide
Previous version documentation (reference only).

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────┐
│         main.py (Main Intelligence)         │
│    Monitors & Recommends Best Device        │
└────────┬─────────────────────┬──────────────┘
         │                     │
    ┌────▼─────┐      ┌───────▼──────┐
    │detect_hw │      │ compute_info  │
    │Hardware  │      │ GPU Monitoring│
    │Detection │      └───┬───────────┘
    └────┬─────┘          │
         │           ┌────▼──────────┐
         │           │get_dgpu_usage │
         │           │NVIDIA Monitor │
         │           └───────────────┘
         │
    ┌────▼──────────────────────────┐
    │   OVMS Server Infrastructure   │
    │ (Model Inference Backend)      │
    │  Port 8000: iGPU               │
    │  Port 8001: NPU                │
    └────────────────────────────────┘
```

---

## 📊 Workflow Example

### 1. System Startup
```bash
# Terminal 1: Detect hardware
python detect_hw.py
```

### 2. Start OVMS Servers
```bash
# Terminal 2: iGPU Server (GPU)
ovms.exe --rest_port 8000 \
  --source_model OpenVINO/Qwen3-8B-int4-ov \
  --model_repository_path models \
  --target_device GPU --cache_size 2 \
  --task text_generation --max_num_batched_tokens 99999

# Terminal 3: NPU Server
ovms.exe --rest_port 8001 \
  --source_model OpenVINO/Qwen3-8B-int4-cw-ov \
  --model_repository_path models \
  --target_device NPU --cache_size 2 \
  --task text_generation --max_num_batched_tokens 99999
```

### 3. Run Main System
```bash
# Terminal 4: Main intelligence system
python main.py
```

### 4. Monitor Performance
```bash
# Terminal 5: Continuous monitoring
python compute_info_1.py
```

### 5. (Optional) Run Tests
```bash
# Find optimal switching threshold
python benchmark_final.py

# Simulate load and test
python usage_load.py --load 0.7
python benchmark_ovms.py
```

---

## ⚙️ Configuration Guide

### Edit `main.py` Model Configuration

```python
MODEL_LIST = {
    "dGPU": ["gpt-oss:20b", "qwen3:14b", "qwen3:8b"],
    "iGPU": ["OpenVINO/Qwen3-8B-int4-ov"],
    "NPU":  ["OpenVINO/Qwen3-8B-int4-cw-ov"]
}

MODEL_VRAM = {
    "gpt-oss:20b": 15,      # GB required
    "qwen3:14b": 12,
    "qwen3:8b": 6,
    "OpenVINO/Qwen3-8B-int4-ov": 0,
    "OpenVINO/Qwen3-8B-int4-cw-ov": 0
}

# iGPU/NPU utilization threshold (0-1)
# When iGPU > 50%, switch to NPU
IGPU_NPU_THRESHOLD = 0.5
```

---

## 📝 Important Notes

### Administrator Privileges
- ⚠️ `battery_health.py` requires admin rights
- ⚠️ `battery_health_mcp.py` requires admin rights
- Auto-elevation is built-in for both scripts

### PyOpenCL Requirements
- ⚠️ `usage_load.py` needs PyOpenCL and Intel iGPU drivers
- Requires OpenCL support on your system

### OVMS Prerequisites
- ⚠️ OVMS server must be pre-downloaded and configured
- ⚠️ Models must be pre-downloaded before running OVMS
- ✅ Ensure OVMS is in system PATH

### Recommended Setup
- ✅ Use Python virtual environment
- ✅ Run OVMS in separate terminal windows
- ✅ Use 4+ terminal windows for full workflow
- ✅ First run: execute `benchmark_final.py` to calibrate system

---

## 🔗 External Resources

- [OpenVINO Official Documentation](https://docs.openvino.ai/)
- [OVMS Deployment Guide](https://docs.openvino.ai/2025/model-server/ovms_docs_deploying_server_baremetal.html)
- [Hugging Face OpenVINO Models](https://huggingface.co/OpenVINO)
- [OpenVINO NPU Deployment](https://docs.openvino.ai/2025/model-server/ovms_demos_llm_npu.html)
- [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit)

---

## 📦 Dependencies

```
openvino-genai==2025.3.0
wmi
requests
numpy
psutil
torch
pyopencl
fastmcp
```

---

## 🎯 Use Cases

| Scenario | Files | Purpose |
|----------|-------|---------|
| Auto device selection | `main.py` | Real-time recommendations |
| Initial setup | `detect_hw.py` | Detect available hardware |
| Performance tuning | `benchmark_final.py` | Find optimal thresholds |
| Load testing | `usage_load.py`, `dgpu_usage.py` | Simulate system load |
| Battery optimization | `battery_health.py` | Extend laptop battery life |
| MCP integration | `battery_health_mcp.py` | Remote tool access |
| Model conversion | `export_model.py` | Convert to OpenVINO format |
| Real-time monitoring | `compute_info_1.py` | Watch GPU usage |

---

## 📄 License

This project is provided as-is for research and educational purposes.

---

## 👨‍💻 Support

For issues or questions:
1. Check the [README_v3.md](README_v3.md) setup guide
2. Verify OVMS is properly installed and running
3. Ensure all dependencies are installed: `pip install -r requirements.txt`
4. Run hardware detection: `python detect_hw.py`
