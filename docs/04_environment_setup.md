# 环境配置说明

## 推荐环境

正式训练建议使用 Python 3.10 或 3.11。

当前机器有 RTX 4060 Laptop GPU，8GB 显存。适合：

- 小模型 smoke test；
- LoRA SFT；
- 短 epoch SFT；
- 小规模超参数对比。

不建议直接上大 hidden size、大 batch、长 epoch。

## 安装建议

```powershell
conda create -n minimind python=3.10
conda activate minimind
cd minimind
pip install -r requirements.txt
```

如果 CUDA/PyTorch 需要单独安装，根据本机 CUDA 驱动选择合适版本。CPU 版也可以用于流程验证：

```powershell
pip install torch torchvision
```

## 最小验证命令

```powershell
python scripts\inspect_fire_dsl_data.py
python fire-dsl-data\tools\demo_verify_dsl.py
python scripts\analyze_tokenizer_terms.py
```

## 常见显存处理

- `batch_size` 从 1 或 2 开始。
- `hidden_size` 从 128 或 256 开始。
- `num_hidden_layers` 从 2 或 4 开始。
- `max_seq_len` 先用 512，再尝试 768。
- 优先尝试 LoRA，而不是盲目增大模型。

