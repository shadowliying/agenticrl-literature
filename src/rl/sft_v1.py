# encoding: utf-8  # 文件编码声明
# SFT 轻量对齐流程（v1）  # 文件用途说明
from __future__ import annotations  # 允许类型前向引用
from dataclasses import dataclass, field  # 数据类与默认工厂
from typing import Any, Dict, List, Optional  # 类型注解
# 以上为标准库导入  # 分隔说明
@dataclass  # 数据类装饰器
class SFTConfig:  # SFT 配置结构
    base_model: str = "Qwen2.5-7B-Instruct"  # 基座模型名称
    output_dir: str = "./outputs/sft_v1"  # 输出目录
    max_seq_len: int = 4096  # 最大序列长度
    batch_size: int = 4  # 批大小
    learning_rate: float = 2e-5  # 学习率
    num_epochs: int = 1  # 训练轮数
    use_lora: bool = True  # 是否使用 LoRA
    lora_r: int = 16  # LoRA rank
    lora_alpha: int = 32  # LoRA alpha
    lora_dropout: float = 0.05  # LoRA dropout
    target_modules: List[str] = field(default_factory=lambda: ["q_proj", "v_proj"])  # LoRA 目标层
    seed: int = 42  # 随机种子
# 以上为 SFT 配置  # 分隔说明
@dataclass  # 数据类装饰器
class SFTSample:  # SFT 样本结构
    instruction: str  # 指令文本
    input: str = ""  # 额外输入
    output: str = ""  # 期望输出
    schema_hint: str = ""  # 输出格式约束提示
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据
# 以上为样本结构  # 分隔说明
def build_prompt(sample: SFTSample) -> str:  # 构建训练提示词
    if sample.input:  # 如果有额外输入
        prompt = f"{sample.instruction}\n\n输入：{sample.input}\n\n格式要求：{sample.schema_hint}".strip()  # 指令+输入+格式
    else:  # 如果没有输入
        prompt = f"{sample.instruction}\n\n格式要求：{sample.schema_hint}".strip()  # 指令+格式
    return prompt  # 返回提示词
# 以上为提示构建  # 分隔说明
def validate_sample(sample: SFTSample) -> List[str]:  # 样本校验
    errors: List[str] = []  # 错误列表
    if not sample.instruction:  # 指令不能为空
        errors.append("instruction is required")  # 添加错误
    if not sample.output:  # 输出不能为空
        errors.append("output is required")  # 添加错误
    return errors  # 返回错误
# 以上为样本校验  # 分隔说明
def to_sft_record(sample: SFTSample) -> Dict[str, str]:  # 生成 SFT 训练样本
    prompt = build_prompt(sample)  # 构建提示词
    return {"prompt": prompt, "response": sample.output}  # 返回标准结构
# 以上为样本转换  # 分隔说明
def load_sft_samples(records: List[Dict[str, Any]]) -> List[SFTSample]:  # 从字典加载样本
    samples: List[SFTSample] = []  # 初始化列表
    for r in records:  # 遍历记录
        sample = SFTSample(  # 构建样本
            instruction=str(r.get("instruction", "")),  # 指令
            input=str(r.get("input", "")),  # 输入
            output=str(r.get("output", "")),  # 输出
            schema_hint=str(r.get("schema_hint", "")),  # 格式提示
            metadata=dict(r.get("metadata", {})),  # 元数据
        )  # 构建结束
        samples.append(sample)  # 加入列表
    return samples  # 返回样本列表
# 以上为样本加载  # 分隔说明
def summarize_config(config: SFTConfig) -> Dict[str, Any]:  # 输出配置摘要
    return {  # 返回字典
        "base_model": config.base_model,  # 基座模型
        "output_dir": config.output_dir,  # 输出目录
        "max_seq_len": config.max_seq_len,  # 最大长度
        "batch_size": config.batch_size,  # 批大小
        "learning_rate": config.learning_rate,  # 学习率
        "num_epochs": config.num_epochs,  # 训练轮数
        "use_lora": config.use_lora,  # 是否 LoRA
        "lora_r": config.lora_r,  # LoRA r
        "lora_alpha": config.lora_alpha,  # LoRA alpha
        "lora_dropout": config.lora_dropout,  # LoRA dropout
        "target_modules": list(config.target_modules),  # 目标层
        "seed": config.seed,  # 随机种子
    }  # 摘要结束
# 以上为配置摘要  # 分隔说明
def run_sft(config: SFTConfig, samples: List[SFTSample]) -> Dict[str, Any]:  # 执行 SFT 入口（占位）
    if not samples:  # 样本为空
        raise ValueError("SFT samples are empty")  # 抛出错误
    for s in samples:  # 遍历样本
        errs = validate_sample(s)  # 校验样本
        if errs:  # 如果存在错误
            raise ValueError(f"invalid sample: {errs}")  # 抛出错误
    records = [to_sft_record(s) for s in samples]  # 转换为训练样本
    return {  # 返回执行摘要
        "config": summarize_config(config),  # 配置摘要
        "num_samples": len(records),  # 样本数量
        "note": "This is a stub for SFT alignment. Integrate with TRL/PEFT in training pipeline.",  # 说明
    }  # 摘要结束
