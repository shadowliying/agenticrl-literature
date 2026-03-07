# encoding: utf-8
# GRPO 训练入口（v1）
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

try:
    import torch
except Exception:  # pragma: no cover - 允许无 torch 环境下查看配置
    torch = None

try:
    from datasets import Dataset
except Exception:  # pragma: no cover - 允许无 datasets 环境下回退
    Dataset = None

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
except Exception:  # pragma: no cover - 允许无 transformers 环境下回退
    AutoModelForCausalLM = None
    AutoTokenizer = None

try:
    from peft import LoraConfig, TaskType
except Exception:  # pragma: no cover - 允许无 peft 环境下回退
    LoraConfig = None
    TaskType = None

try:
    from trl import GRPOConfig as TRLGRPOConfig, GRPOTrainer
except Exception:  # pragma: no cover - 允许无 trl 环境下回退
    TRLGRPOConfig = None
    GRPOTrainer = None


RewardFn = Callable[..., List[float]]


@dataclass
class RewardWeights:
    r_quality: float
    r_sufficiency: float
    r_info_gain: float
    r_efficiency: float


@dataclass
class GRPOConfig:
    base_model: str = "Qwen2.5-7B-Instruct"
    output_dir: str = "./outputs/grpo_v1"
    max_prompt_length: int = 3072
    max_completion_length: int = 512
    learning_rate: float = 5e-6
    num_generations: int = 4
    beta: float = 0.04
    total_steps: int = 1000
    logging_steps: int = 10
    save_steps: int = 200
    seed: int = 42
    trust_remote_code: bool = True

    use_lora: bool = True
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: list[str] = field(default_factory=lambda: ["q_proj", "v_proj"])

    bf16: bool = True
    phase_switch_ratio: float = 0.60


PHASE1_WEIGHTS = RewardWeights(
    r_quality=0.25,
    r_sufficiency=0.35,
    r_info_gain=0.25,
    r_efficiency=0.15,
)

PHASE2_WEIGHTS = RewardWeights(
    r_quality=0.40,
    r_sufficiency=0.25,
    r_info_gain=0.20,
    r_efficiency=0.15,
)


def framework_status() -> Dict[str, bool]:
    return {
        "torch": torch is not None,
        "datasets": Dataset is not None,
        "transformers": AutoModelForCausalLM is not None and AutoTokenizer is not None,
        "peft": LoraConfig is not None,
        "trl": GRPOTrainer is not None and TRLGRPOConfig is not None,
    }


def missing_training_dependencies() -> List[str]:
    status = framework_status()
    return [name for name, installed in status.items() if not installed]


def compute_reward(
    weights: RewardWeights,
    r_quality: float,
    r_sufficiency: float,
    r_info_gain: float,
    r_efficiency: float,
    r_penalty: float = 0.0,
) -> float:
    return (
        weights.r_quality * r_quality
        + weights.r_sufficiency * r_sufficiency
        + weights.r_info_gain * r_info_gain
        + weights.r_efficiency * r_efficiency
        - r_penalty
    )


def reward_breakdown(
    weights: RewardWeights,
    metrics: Dict[str, float],
    penalty: float = 0.0,
) -> Dict[str, float]:
    quality_term = weights.r_quality * float(metrics.get("r_quality", 0.0))
    sufficiency_term = weights.r_sufficiency * float(metrics.get("r_sufficiency", 0.0))
    info_gain_term = weights.r_info_gain * float(metrics.get("r_info_gain", 0.0))
    efficiency_term = weights.r_efficiency * float(metrics.get("r_efficiency", 0.0))
    total = quality_term + sufficiency_term + info_gain_term + efficiency_term - penalty
    return {
        "quality_term": round(quality_term, 4),
        "sufficiency_term": round(sufficiency_term, 4),
        "info_gain_term": round(info_gain_term, 4),
        "efficiency_term": round(efficiency_term, 4),
        "penalty": round(penalty, 4),
        "total_reward": round(total, 4),
    }


def select_phase(
    step: int,
    total_steps: int,
    sufficiency_avg: float = 0.0,
    info_gain_avg: float = 0.0,
    phase_switch_ratio: float = 0.60,
) -> Dict[str, float]:
    if total_steps <= 0:
        return PHASE1_WEIGHTS.__dict__
    ratio = step / total_steps
    if ratio >= phase_switch_ratio:
        return PHASE2_WEIGHTS.__dict__
    if sufficiency_avg >= 0.75 and info_gain_avg >= 0.5:
        return PHASE2_WEIGHTS.__dict__
    return PHASE1_WEIGHTS.__dict__


def load_records_from_path(path: str) -> List[Dict[str, Any]]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"dataset file not found: {path}")

    if file_path.suffix.lower() == ".jsonl":
        records: List[Dict[str, Any]] = []
        for line in file_path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
        return records

    if file_path.suffix.lower() == ".json":
        payload = json.loads(file_path.read_text(encoding="utf-8-sig"))
        if isinstance(payload, list):
            return [dict(item) for item in payload]
        raise ValueError("json dataset must be a list of records")

    raise ValueError("only .jsonl or .json dataset files are supported")


def normalize_grpo_record(record: Dict[str, Any]) -> Dict[str, Any]:
    prompt = str(record.get("prompt") or record.get("question") or record.get("instruction") or "").strip()
    if not prompt:
        raise ValueError("GRPO record requires prompt/question/instruction")
    return {
        "prompt": prompt,
        "metadata": dict(record.get("metadata", {})),
    }


def build_dataset(records: Sequence[Dict[str, Any]]) -> Any:
    normalized = [normalize_grpo_record(record) for record in records]
    if Dataset is not None:
        return Dataset.from_list(normalized)
    return normalized


def build_lora_config(config: GRPOConfig) -> Any:
    payload = {
        "r": config.lora_r,
        "lora_alpha": config.lora_alpha,
        "lora_dropout": config.lora_dropout,
        "target_modules": list(config.target_modules),
        "bias": "none",
        "task_type": "CAUSAL_LM",
    }
    if not config.use_lora or LoraConfig is None:
        return payload
    return LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        target_modules=list(config.target_modules),
        bias="none",
        task_type=TaskType.CAUSAL_LM if TaskType is not None else "CAUSAL_LM",
    )


def build_trl_grpo_config(config: GRPOConfig) -> Any:
    payload = {
        "output_dir": config.output_dir,
        "learning_rate": config.learning_rate,
        "max_prompt_length": config.max_prompt_length,
        "max_completion_length": config.max_completion_length,
        "num_generations": config.num_generations,
        "beta": config.beta,
        "logging_steps": config.logging_steps,
        "save_steps": config.save_steps,
        "seed": config.seed,
        "bf16": config.bf16,
    }
    if TRLGRPOConfig is None:
        return payload
    return TRLGRPOConfig(**payload)


def summarize_config(config: GRPOConfig) -> Dict[str, Any]:
    payload = asdict(config)
    payload["phase1_weights"] = asdict(PHASE1_WEIGHTS)
    payload["phase2_weights"] = asdict(PHASE2_WEIGHTS)
    return payload


def example_launch_commands() -> List[str]:
    return [
        "python src/rl/grpo_v1.py --train-file data/rl_rollout_train.jsonl --dry-run",
        "python src/rl/grpo_v1.py --train-file data/rl_rollout_train.jsonl --output-dir ./outputs/grpo_v1 --run-train",
        "accelerate launch --num_processes 2 src/rl/grpo_v1.py --train-file data/rl_rollout_train.jsonl --output-dir ./outputs/grpo_v1 --run-train",
    ]


def build_grpo_runtime_spec(config: GRPOConfig, train_records: Optional[Sequence[Dict[str, Any]]] = None) -> Dict[str, Any]:
    preview = [normalize_grpo_record(record) for record in list(train_records or [])[:2]]
    return {
        "framework": "PyTorch + Transformers + PEFT/LoRA + TRL",
        "dependency_status": framework_status(),
        "missing_dependencies": missing_training_dependencies(),
        "config": summarize_config(config),
        "trainer": "TRL.GRPOTrainer",
        "reward_shape": {
            "phase1": asdict(PHASE1_WEIGHTS),
            "phase2": asdict(PHASE2_WEIGHTS),
            "phase_switch_ratio": config.phase_switch_ratio,
        },
        "sample_preview": preview,
        "startup_commands": example_launch_commands(),
        "note": "GRPO 阶段优化的是 Orchestrator 的检索/停止/replan 策略，而不是单纯答案措辞。",
    }


def _completion_to_text(completion: Any) -> str:
    if isinstance(completion, str):
        return completion
    if isinstance(completion, dict):
        return str(completion.get("content", ""))
    if isinstance(completion, list):
        return " ".join(_completion_to_text(item) for item in completion)
    return str(completion)


def _normalize_score_list(values: Any, expected_size: int, default: float = 0.0) -> List[float]:
    if isinstance(values, (int, float)):
        return [float(values)] * expected_size
    if isinstance(values, list):
        normalized = [float(v) for v in values[:expected_size]]
        if len(normalized) < expected_size:
            normalized.extend([default] * (expected_size - len(normalized)))
        return normalized
    return [default] * expected_size


def build_trl_reward_function(config: GRPOConfig) -> RewardFn:
    def reward_func(prompts: Sequence[Any], completions: Sequence[Any], **kwargs: Any) -> List[float]:
        batch_size = len(completions)
        step = int(kwargs.get("step", 0))
        weights_map = select_phase(
            step=step,
            total_steps=config.total_steps,
            sufficiency_avg=float(kwargs.get("sufficiency_avg", 0.0)),
            info_gain_avg=float(kwargs.get("info_gain_avg", 0.0)),
            phase_switch_ratio=config.phase_switch_ratio,
        )
        weights = RewardWeights(**weights_map)

        quality_scores = _normalize_score_list(kwargs.get("quality_scores"), batch_size, 0.0)
        sufficiency_scores = _normalize_score_list(kwargs.get("sufficiency_scores"), batch_size, 0.0)
        info_gain_scores = _normalize_score_list(kwargs.get("info_gain_scores"), batch_size, 0.0)
        penalty_scores = _normalize_score_list(kwargs.get("penalties"), batch_size, 0.0)

        rewards: List[float] = []
        for idx, completion in enumerate(completions):
            completion_text = _completion_to_text(completion)
            length_ratio = min(len(completion_text) / max(config.max_completion_length, 1), 1.0)
            efficiency_score = max(0.0, 1.0 - length_ratio)
            rewards.append(
                compute_reward(
                    weights=weights,
                    r_quality=quality_scores[idx],
                    r_sufficiency=sufficiency_scores[idx],
                    r_info_gain=info_gain_scores[idx],
                    r_efficiency=efficiency_score,
                    r_penalty=penalty_scores[idx],
                )
            )
        return rewards

    return reward_func


def build_grpo_trainer(
    config: GRPOConfig,
    train_records: Sequence[Dict[str, Any]],
) -> Any:
    if missing_training_dependencies():
        raise ImportError(f"missing training dependencies: {', '.join(missing_training_dependencies())}")

    model = AutoModelForCausalLM.from_pretrained(
        config.base_model,
        trust_remote_code=config.trust_remote_code,
        torch_dtype=torch.bfloat16 if torch is not None and config.bf16 else None,
    )
    tokenizer = AutoTokenizer.from_pretrained(config.base_model, use_fast=False, trust_remote_code=config.trust_remote_code)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    trainer = GRPOTrainer(
        model=model,
        processing_class=tokenizer,
        args=build_trl_grpo_config(config),
        train_dataset=build_dataset(train_records),
        peft_config=build_lora_config(config) if config.use_lora else None,
        reward_funcs=build_trl_reward_function(config),
    )
    return trainer


def run_grpo(
    config: GRPOConfig,
    train_records: Sequence[Dict[str, Any]],
    dry_run: bool = True,
) -> Dict[str, Any]:
    runtime_spec = build_grpo_runtime_spec(config, train_records=train_records)
    if dry_run:
        runtime_spec["mode"] = "dry_run"
        return runtime_spec

    trainer = build_grpo_trainer(config=config, train_records=train_records)
    train_result = trainer.train()
    trainer.save_model(config.output_dir)
    runtime_spec["mode"] = "train"
    runtime_spec["train_result"] = str(train_result)
    return runtime_spec


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GRPO trainer entrypoint for Orchestrator policy optimization.")
    parser.add_argument("--train-file", required=True, help="Path to GRPO prompt dataset in jsonl/json format.")
    parser.add_argument("--base-model", default="Qwen2.5-7B-Instruct")
    parser.add_argument("--output-dir", default="./outputs/grpo_v1")
    parser.add_argument("--max-prompt-length", type=int, default=3072)
    parser.add_argument("--max-completion-length", type=int, default=512)
    parser.add_argument("--learning-rate", type=float, default=5e-6)
    parser.add_argument("--num-generations", type=int, default=4)
    parser.add_argument("--total-steps", type=int, default=1000)
    parser.add_argument("--phase-switch-ratio", type=float, default=0.60)
    parser.add_argument("--run-train", action="store_true", help="Run trainer.train() instead of dry-run.")
    parser.add_argument("--no-lora", action="store_true", help="Disable LoRA and return full-finetune style config.")
    parser.add_argument("--bf16", action="store_true", default=True)
    return parser


def config_from_args(args: argparse.Namespace) -> GRPOConfig:
    return GRPOConfig(
        base_model=args.base_model,
        output_dir=args.output_dir,
        max_prompt_length=args.max_prompt_length,
        max_completion_length=args.max_completion_length,
        learning_rate=args.learning_rate,
        num_generations=args.num_generations,
        total_steps=args.total_steps,
        phase_switch_ratio=args.phase_switch_ratio,
        use_lora=not args.no_lora,
        bf16=bool(args.bf16),
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    config = config_from_args(args)
    train_records = load_records_from_path(args.train_file)
    result = run_grpo(config=config, train_records=train_records, dry_run=not args.run_train)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
