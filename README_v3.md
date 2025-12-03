
# 創建虛擬環境並安裝 OpenVINO™ GenAI 套件
https://docs.openvino.ai/2025/get-started/install-openvino.html?PACKAGE=OPENVINO_GENAI&VERSION=v_2025_3_0&OP_SYSTEM=WINDOWS&DISTRIBUTION=PIP

### Step 1: Create virtual environment
```bash
python -m venv openvino_env
```

### Step 2: Activate virtual environment
```bash
openvino_env\Scripts\activate
```

### Step 3: Upgrade pip to latest version
```bash
python -m pip install --upgrade pip
```

### Step 4: Download and install the package
```bash
pip install openvino-genai==2025.3.0
```

---

# 下載並安裝 OpenVINO™ Model Server (OVMS)

https://docs.openvino.ai/2025/model-server/ovms_docs_deploying_server_baremetal.html

### Step 1 : 下載 OVMS 

```bash
curl -L https://github.com/openvinotoolkit/model_server/releases/download/v2025.3/ovms_windows_python_on.zip -o ovms.zip
```

### Step 2 : 解壓縮

```bash
tar -xf ovms.zip
```

---

# 設置環境變數與下載 Models

### Step 1 : 設置**臨時**環境變數

```bash
cd ovms
setupvars.bat
```
### Step 1.1 : 設置**永久**環境變數

1. 將 `.\ov\ovms` 加入系統環境變數 Path 中，並放置最上方
2. 將 `.\ov\ovms\python` 加入系統環境變數 Path 中，並放置第二個位置
3. 將 `.\ov\ovms\python\Scripts` 加入系統環境變數 Path 中，並放置第三個位置

### Step 2 : 下載 Models ( 跑在 CPU, GPU )

https://docs.openvino.ai/2025/model-server/ovms_demos_continuous_batching_agent.html#direct-pulling-of-pre-configured-huggingface-models-on-windows

```bash
ovms.exe --pull --model_repository_path models --source_model OpenVINO/Qwen3-8B-int4-ov --task text_generation --tool_parser hermes3
```

### Step 2.1 : 下載 Models ( 跑在 NPU ) 

```bash
ovms.exe --pull --model_repository_path models --source_model OpenVINO/Qwen3-8B-int4-cw-ov --task text_generation --tool_parser hermes3
```

--- 

# 啟動 OVMS 伺服器 (單一模型)

https://docs.openvino.ai/2025/model-server/ovms_demos_continuous_batching_agent.html#deploying-on-windows-with-gpu

* 將模型跑在 GPU 範例 : 
```bash
ovms.exe --rest_port 8000 --source_model OpenVINO/Qwen3-8B-int4-ov --model_repository_path models --tool_parser hermes3 --target_device GPU --cache_size 2 --task text_generation --max_num_batched_tokens 99999
```

* 將模型跑在 NPU 範例 : 
```bash
ovms.exe --rest_port 8000 --source_model OpenVINO/Qwen3-8B-int4-cw-ov --model_repository_path models --target_device NPU --cache_size 2 --task text_generation --max_num_batched_tokens 99999
```

# 啟動 OVMS 伺服器 (多模型)

### Step1 : 將模型新增至 `config.json` 檔案當中

```
ovms --model_name <model name> --model_path <model absolute path> --add_to_config <config.json absolute path>
```
範例 : 
```
ovms --model_name Qwen3-8B-int4-ov --model_path  "C:\Users\ZPL\Desktop\ov\ovms\models\OpenVINO\Qwen3-8B-int4-ov" --add_to_config c:\Users\ZPL\Desktop\ov\config.json
```

### Step2 : 設定模型存放的裝置
將模型資料夾底下的 `graph.pbtxt` 檔案當中的 `device: "NPU"` 修改成 `device: "GPU"` 即可運行至 GPU。

### Step3 : 使用 `config.json` 啟動 OVMS 伺服器
```
ovms --config_path <config.json absolute path> --rest_port 8000
```
範例 : 
```bash
ovms --config_path c:\Users\ZPL\Desktop\ov\config.json --rest_port 8000
```

# 測試 OVMS 伺服器
可連線至 http://localhost:8000/v1/config ，查看是否有回傳JSON格式的資訊。

回傳範例 :
```json
{
"DeepSeek-R1-Distill-Qwen-1.5B-int4-cw-ov" : 
{
 "model_version_status": [
  {
   "version": "1",
   "state": "AVAILABLE",
   "status": {
    "error_code": "OK",
    "error_message": "OK"
   }
  }
 ]
},
"Qwen3-8B-int4-cw-ov" : 
{
 "model_version_status": [
  {
   "version": "1",
   "state": "AVAILABLE",
   "status": {
    "error_code": "OK",
    "error_message": "OK"
   }
  }
 ]
}
}
```
當顯示 OK 即代表伺服器已成功啟動並載入模型。

# 測試模型回應

```bash
curl http://localhost:8000/v3/chat/completions -H "Content-Type: application/json" -d "{\"model\":\"Qwen3-8B-int4-ov\",\"messages\":[{\"role\":\"system\",\"content\":\"You are a helpful assistant.\"},{\"role\":\"user\",\"content\":\"Say this is a test\"}]}"
```

# 使用 NPU aacceleration
https://docs.openvino.ai/2025/model-server/ovms_demos_llm_npu.html

### Step1 : 下載 `export_model.py` 檔案
```bash
curl https://raw.githubusercontent.com/openvinotoolkit/model_server/refs/heads/releases/2025/3/demos/common/export_models/export_model.py -o export_model.py
```

### Step2 : 安裝相關套件
```bash
pip3 install -r https://raw.githubusercontent.com/openvinotoolkit/model_server/refs/heads/releases/2025/3/demos/common/export_models/requirements.txt
```

### Step3 : 下載模型，並轉換成ov格式
```bash
python export_model.py text_generation --source_model <model name> --target_device NPU --config_file_path models/config.json --ov_cache_dir ./models/.ov_cache --model_repository_path models --overwrite_models
```
範例 :
```bash
python export_model.py text_generation --source_model Qwen/Qwen3-4B --target_device NPU --config_file_path models/config.json --ov_cache_dir ./models/.ov_cache --model_repository_path models --overwrite_models
```

# 將ov 模型整合至 OpenWebUI 設定
https://docs.openvino.ai/2025/model-server/ovms_demos_integration_with_open_webui.html

# 模型連結
* https://huggingface.co/OpenVINO
* https://huggingface.co/collections/OpenVINO/llm-6687aaa2abca3bbcec71a9bd
* https://huggingface.co/collections/OpenVINO/llms-optimized-for-npu-686e7f0bf7bc184bd71f8ba0