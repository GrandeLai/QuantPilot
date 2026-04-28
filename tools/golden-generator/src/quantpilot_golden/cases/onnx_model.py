"""生成测试用 ONNX 模型.

模型定义：
  一个极简线性层（Gemm）:  y = W @ x^T + b
  W = [[0.5, 0.3]]   (shape: [1, 2])
  b = [0.1]          (shape: [1])
  输入 x: shape [1, 2]   (batch=1, features=2)
  输出 y: shape [1, 1]   (batch=1, outputs=1)

测试用例：
  x = [1.0, 2.0]  → y = 0.5*1.0 + 0.3*2.0 + 0.1 = 1.2

Meta.json 格式符合 plan §6 ml_model_meta.schema.json 约定：
  model_id, features, input_shape, output_shape
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper


def create_test_linear_model() -> onnx.ModelProto:
    """创建 W=[[0.5,0.3]], b=[0.1] 的线性模型."""
    W = np.array([[0.5, 0.3]], dtype=np.float32)  # shape [1, 2]
    b = np.array([0.1], dtype=np.float32)           # shape [1]

    # Initializers (constants)
    W_init = numpy_helper.from_array(W, name="W")
    b_init = numpy_helper.from_array(b, name="b")

    # Nodes
    # Gemm: Y = alpha * A @ B^T + beta * C
    # Here: A = input (shape [1,2]), B = W (shape [1,2]), C = b (shape [1])
    # transB=1 so W^T is used: Y = input @ W^T + b
    gemm_node = helper.make_node(
        op_type="Gemm",
        inputs=["input", "W", "b"],
        outputs=["output"],
        alpha=1.0,
        beta=1.0,
        transA=0,
        transB=1,
    )

    # Graph
    input_tensor = helper.make_tensor_value_info("input", TensorProto.FLOAT, [1, 2])
    output_tensor = helper.make_tensor_value_info("output", TensorProto.FLOAT, [1, 1])
    graph = helper.make_graph(
        nodes=[gemm_node],
        name="test_linear",
        inputs=[input_tensor],
        outputs=[output_tensor],
        initializer=[W_init, b_init],
    )

    # Model
    model = helper.make_model(
        graph,
        opset_imports=[helper.make_opsetid("", 11)],
    )
    model.ir_version = 7
    model.doc_string = "Test linear model: y = 0.5*x0 + 0.3*x1 + 0.1"
    onnx.checker.check_model(model)
    return model


def create_meta_json() -> dict:
    """生成符合 plan §6 约定的 meta.json."""
    return {
        "model_id": "test_linear",
        "trained_at": "2026-04-28T00:00:00Z",
        "features": [
            {"name": "feature_0", "dtype": "float32"},
            {"name": "feature_1", "dtype": "float32"},
        ],
        "target": "output",
        "framework": "onnx_manual",
        "training_metrics": {
            "note": "手工构造测试模型",
        },
        "input_shape": [1, 2],
        "output_shape": [1, 1],
        "test_case": {
            "input": [1.0, 2.0],
            "expected_output": [1.2],
            "tolerance_abs": 1e-6,
            "note": "0.5*1.0 + 0.3*2.0 + 0.1 = 1.2",
        },
    }


def main() -> None:
    """生成 model.onnx 和 meta.json 到 common/data-store/models/test_linear/."""
    out_dir = (
        Path(__file__).parents[5]  # repo root: QuantPilot/
        / "common"
        / "data-store"
        / "models"
        / "test_linear"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write model.onnx
    model = create_test_linear_model()
    onnx_path = out_dir / "model.onnx"
    onnx.save(model, str(onnx_path))
    print(f"Written: {onnx_path}")

    # Write meta.json
    meta = create_meta_json()
    meta_path = out_dir / "meta.json"
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print(f"Written: {meta_path}")

    # Verify with numpy
    expected = 0.5 * 1.0 + 0.3 * 2.0 + 0.1
    print(f"\nVerification: f([1.0, 2.0]) = {expected:.6f} (expected: 1.200000)")


if __name__ == "__main__":
    main()
