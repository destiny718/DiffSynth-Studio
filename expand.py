#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import re
from pathlib import Path

import pandas as pd


def infer_video_column(df: pd.DataFrame) -> str:
    """
    自动推断哪一列是 video 路径列：
    优先使用常见列名，其次找“非空值大多以 .mp4 结尾”的第一列。
    """
    common_names = [
        "video", "video_path", "mp4", "path",
        "driving_video", "source_video", "ref_video"
    ]
    for c in common_names:
        if c in df.columns:
            return c

    best_col = None
    best_ratio = 0.0
    for c in df.columns:
        s = df[c].dropna().astype(str)
        if len(s) == 0:
            continue
        ratio = (s.str.lower().str.endswith(".mp4")).mean()
        if ratio > best_ratio:
            best_ratio = ratio
            best_col = c

    if best_col is None or best_ratio < 0.5:
        raise ValueError(
            "未能自动找到 video 路径列。请用 --video-col 指定，例如 --video-col video"
        )
    return best_col


def to_position_path(p: str) -> str:
    """
    把路径最后的 xxx.mp4 替换成 position.mp4（兼容 / 和 \\）。
    """
    p = str(p)
    newp = re.sub(r"[^/\\]+\.mp4$", "position.mp4", p, flags=re.IGNORECASE)
    if newp == p:
        # 如果末尾不是 .mp4，就按“同目录下 position.mp4”处理
        try:
            return str(Path(p).parent / "position.mp4")
        except Exception:
            return p + "/position.mp4"
    return newp


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        default="/data/tianqi/DiffSynth-Studio/dataset_metadata.csv",
        help="输入 CSV 路径",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="输出 CSV 路径（默认覆盖原文件）",
    )
    parser.add_argument(
        "--video-col",
        default=None,
        help="指定用于生成 position_video 的 video 路径列名（不填则自动推断）",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    out_path = Path(args.out) if args.out else csv_path

    df = pd.read_csv(csv_path)

    video_col = args.video_col or infer_video_column(df)
    df["position_video"] = df[video_col].astype(str).apply(to_position_path)

    df.to_csv(out_path, index=False)
    print(f"Done. video_col={video_col}, written to: {out_path}")


if __name__ == "__main__":
    main()