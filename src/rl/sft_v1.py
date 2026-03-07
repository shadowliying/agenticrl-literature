# encoding: utf-8
# SFT 训练入口（v1）
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

try:
    import torch
except Exception:  # pragma: no cover - 允许无 torch 环境下查看配置
    torch = None

try:
    from datasets import Dataset
except Exception:  # pragma: no cover - 允许无 datasets 环境下回退
    Dataset = None

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
except Exception:  # pragma: no cover - 允许无 transformers 环境下回退
    AutoModelForCausalLM = None
    AutoTokenizer = None
    TrainingArguments = None

try:
    from peft import LoraConfig, TaskType
except Exception:  # pragma: no cover - 允许无 peft 环境下回退
    LoraConfig = None
    TaskType = None

try:
    from trl import SFTTrainer
except Exception:  # pragma: no cover - 允许无 trl 环境下回退
    SFTTrainer = None


@dataclass
class SFTConfig:
    base_model: str = "Qwen2.5-7B-Instruct"
    output_dir: str = "./outputs/sft_v1"
    max_seq_len: int = 4096
    per_device_train_batch_size: int = 1
    gradient_accumulation_steps: int = 8
    learning_rate: float = 2e-5
    num_train_epochs: int = 1
    warmup_ratio: float = 0.03
    logging_steps: int = 10
    save_steps: int = 200
    save_total_limit: int = 2
    seed: int = 42
    trust_remote_code: bool = True

    use_lora: bool = True
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: List[str] = field(default_factory=lambda: ["q_proj", "v_proj"])

    bf16: bool = True
    fp16: bool = False
    gradient_checkpointing: bool = True
    report_to: str = "none"


@dataclass
class SFTSample:
    instruction: str
    input: str = ""
    output: str = ""
    schema_hint: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


def framework_status() -> Dict[str, bool]:
    return {
        "torch": torch is not None,
        "datasets": Dataset is not None,
        "transformers": AutoModelForCausalLM is not None and AutoTokenizer is not None and TrainingArguments is not None,
        "peft": LoraConfig is not None,
        "trl": SFTTrainer is not None,
    }


def missing_training_dependencies() -> List[str]:
    status = framework_status()
    missing: List[str] = []
    for name, installed in status.items():
        if not installed:
            missing.append(name)
    return missing


def build_prompt(sample: SFTSample) -> str:
    base_instruction = sample.instruction.strip()
    if sample.input:
        return f"{base_instruction}\n\n输入：{sample.input}\n\n格式要求：{sample.schema_hint}".strip()
    return f"{base_instruction}\n\n格式要求：{sample.schema_hint}".strip()


def validate_sample(sample: SFTSample) -> List[str]:
    errors: List[str] = []
    if not sample.instruction:
        errors.append("instruction is required")
    if not sample.output:
        errors.append("output is required")
    return errors


def to_sft_record(sample: SFTSample) -> Dict[str, Any]:
    prompt = build_prompt(sample)
    text = f"{prompt}\n\n{sample.output}".strip()
    return {
        "prompt": prompt,
        "response": sample.output,
        "text": text,
        "metadata": dict(sample.metadata),
    }


def load_sft_samples(records: Sequence[Dict[str, Any]]) -> List[SFTSample]:
    samples: List[SFTSample] = []
    for record in records:
        samples.append(
            SFTSample(
                instruction=str(record.get("instruction", "")),
                input=str(record.get("input", "")),
                output=str(record.get("output", "")),
                schema_hint=str(record.get("schema_hint", "")),
                metadata=dict(record.get("metadata", {})),
            )
        )
    return samples


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


def load_sft_samples_from_path(path: str) -> List[SFTSample]:
    return load_sft_samples(load_records_from_path(path))


def build_dataset(samples: Sequence[SFTSample]) -> Any:
    records = [to_sft_record(sample) for sample in samples]
    if Dataset is not None:
        return Dataset.from_list(records)
    return records


def build_lora_config(config: SFTConfig) -> Any:
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


def build_training_arguments(config: SFTConfig) -> Any:
    payload = {
        "output_dir": config.output_dir,
        "per_device_train_batch_size": config.per_device_train_batch_size,
        "gradient_accumulation_steps": config.gradient_accumulation_steps,
        "learning_rate": config.learning_rate,
        "num_train_epochs": config.num_train_epochs,
        "warmup_ratio": config.warmup_ratio,
        "logging_steps": config.logging_steps,
        "save_steps": config.save_steps,
        "save_total_limit": config.save_total_limit,
        "bf16": config.bf16,
        "fp16": config.fp16,
        "gradient_checkpointing": config.gradient_checkpointing,
        "report_to": config.report_to,
        "seed": config.seed,
        "remove_unused_columns": False,
    }
    if TrainingArguments is None:
        return payload
    return TrainingArguments(**payload)


def summarize_config(config: SFTConfig) -> Dict[str, Any]:
    return asdict(config)


def example_launch_commands() -> List[str]:
    return [
        "python src/rl/sft_v1.py --train-file data/sft_train.jsonl --dry-run",
        "python src/rl/sft_v1.py --train-file data/sft_train.jsonl --eval-file data/sft_eval.jsonl --output-dir ./outputs/sft_v1 --run-train",
        "accelerate launch --num_processes 2 src/rl/sft_v1.py --train-file data/sft_train.jsonl --eval-file data/sft_eval.jsonl --output-dir ./outputs/sft_v1 --run-train",
    ]


def build_sft_runtime_spec(config: SFTConfig, samples: Sequence[SFTSample]) -> Dict[str, Any]:
    records = [to_sft_record(sample) for sample in samples]
    return {
        "framework": "PyTorch + Transformers + PEFT/LoRA + TRL",
        "dependency_status": framework_status(),
        "missing_dependencies": missing_training_dependencies(),
        "config": summarize_config(config),
        "num_samples": len(records),
        "sample_preview": records[:2],
        "lora_config": build_lora_config(config),
        "training_arguments": build_training_arguments(config),
        "startup_commands": example_launch_commands(),
        "note": "SFT 训练对象是 Orchestrator 的结构化 plan / state->action 对齐，不是单纯答案润色。",
    }


def build_sft_trainer(
    config: SFTConfig,
    samples: Sequence[SFTSample],
    eval_samples: Optional[Sequence[SFTSample]] = None,
) -> Any:
    if missing_training_dependencies():
        raise ImportError(f"missing training dependencies: {', '.join(missing_training_dependencies())}")

    train_dataset = build_dataset(samples)
    eval_dataset = build_dataset(eval_samples or []) if eval_samples else None

    tokenizer = AutoTokenizer.from_pretrained(config.base_model, use_fast=False, trust_remote_code=config.trust_remote_code)
    model = AutoModelForCausalLM.from_pretrained(
        config.base_model,
        trust_remote_code=config.trust_remote_code,
        torch_dtype=torch.bfloat16 if torch is not None and config.bf16 else None,
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        dataset_text_field="text",
        max_seq_length=config.max_seq_len,
        args=build_training_arguments(config),
        peft_config=build_lora_config(config) if config.use_lora else None,
    )
    return trainer


def run_sft(
    config: SFTConfig,
    samples: Sequence[SFTSample],
    eval_samples: Optional[Sequence[SFTSample]] = None,
    dry_run: bool = True,
) -> Dict[str, Any]:
    validated_samples = list(samples)
    if not validated_samples:
        raise ValueError("SFT samples are empty")

    for sample in validated_samples:
        errors = validate_sample(sample)
        if errors:
            raise ValueError(f"invalid sample: {errors}")

    runtime_spec = build_sft_runtime_spec(config, validated_samples)
    if dry_run:
        runtime_spec["mode"] = "dry_run"
        return runtime_spec

    trainer = build_sft_trainer(config=config, samples=validated_samples, eval_samples=eval_samples)
    train_result = trainer.train()
    trainer.save_model(config.output_dir)
    runtime_spec["mode"] = "train"
    runtime_spec["train_result"] = str(train_result)
    return runtime_spec


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SFT trainer entrypoint for Orchestrator policy alignment.")
    parser.add_argument("--train-file", required=True, help="Path to SFT dataset in jsonl/json format.")
    parser.add_argument("--eval-file", default="", help="Optional eval dataset path.")
    parser.add_argument("--base-model", default="Qwen2.5-7B-Instruct")
    parser.add_argument("--output-dir", default="./outputs/sft_v1")
    parser.add_argument("--max-seq-len", type=int, default=4096)
    parser.add_argument("--per-device-train-batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--num-train-epochs", type=int, default=1)
    parser.add_argument("--run-train", action="store_true", help="Run trainer.train() instead of dry-run.")
    parser.add_argument("--no-lora", action="store_true", help="Disable LoRA and return full-finetune style config.")
    parser.add_argument("--bf16", action="store_true", default=True)
    parser.add_argument("--fp16", action="store_true", default=False)
    return parser


def config_from_args(args: argparse.Namespace) -> SFTConfig:
    return SFTConfig(
        base_model=args.base_model,
        output_dir=args.output_dir,
        max_seq_len=args.max_seq_len,
        per_device_train_batch_size=args.per_device_train_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        num_train_epochs=args.num_train_epochs,
        use_lora=not args.no_lora,
        bf16=bool(args.bf16),
        fp16=bool(args.fp16),
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    config = config_from_args(args)
    train_samples = load_sft_samples_from_path(args.train_file)
    eval_samples = load_sft_samples_from_path(args.eval_file) if args.eval_file else None

    result = run_sft(
        config=config,
        samples=train_samples,
        eval_samples=eval_samples,
        dry_run=not args.run_train,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
