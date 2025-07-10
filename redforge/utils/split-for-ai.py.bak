#!/usr/bin/env python
"""
split-for-ai.py --repo . --max-lines 800 --db .chroma
"""
import argparse
import os
import pathlib
import textwrap
from typing import List
from tqdm import tqdm
import chromadb
from chromadb.utils import embedding_functions

EMB_SIZE = 1536  # openai ada-002

def chunk_lines(lines: List[str], max_lines: int = 800):
    for i in range(0, len(lines), max_lines):
        yield lines[i : i + max_lines]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--max-lines", type=int, default=800)
    ap.add_argument("--db", default=".chroma")
    args = ap.parse_args()

    repo = pathlib.Path(args.repo).resolve()
    
    # 创建ChromaDB客户端
    chroma_client = chromadb.PersistentClient(path=args.db)
    
    # 创建embedding函数
    embed_fn = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="text-embedding-3-small",
    )
    
    # 修复：正确的collection创建方式
    try:
        coll = chroma_client.get_collection("promptstrike")
        print("✅ 使用现有collection")
    except:
        coll = chroma_client.create_collection(
            name="promptstrike", 
            embedding_function=embed_fn
        )
        print("✅ 创建新collection")

    processed_files = 0
    
    for path in tqdm(repo.rglob("*")):
        if path.is_dir():
            continue
            
        # 跳过不需要的目录
        if any(part in {".git", ".venv", "node_modules", ".chroma", "ai-chunks", "__pycache__"} 
               for part in path.parts):
            continue
            
        # 跳过非文本文件
        if path.suffix.lower() in {'.pyc', '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip'}:
            continue
            
        rel = path.relative_to(repo)
        
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception as e:
            print(f"⚠️ 跳过文件 {rel}: {e}")
            continue
            
        if len(text) == 0:
            continue

        # 分块处理
        if len(text) <= args.max_lines:
            chunks = [text]
        else:
            chunks = list(chunk_lines(text, args.max_lines))

        for idx, chunk in enumerate(chunks):
            doc_id = f"{rel}::ck{idx}"
            content = "\n".join(chunk)
            
            # 添加到ChromaDB
            try:
                coll.add(
                    ids=[doc_id], 
                    documents=[content], 
                    metadatas=[{"path": str(rel), "idx": idx}]
                )
            except Exception as e:
                print(f"⚠️ ChromaDB添加失败 {doc_id}: {e}")
                continue

            # 保存到文件便于查看
            out_dir = repo / "ai-chunks" / rel.parent
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{rel.stem}_ck{idx}.md"
            
            if not out_path.exists():
                try:
                    out_path.write_text(
                        f"<!-- source: {rel} idx:{idx} -->\n\n```{path.suffix[1:] if path.suffix else 'text'}\n{content}\n```",
                        encoding="utf-8"
                    )
                except Exception as e:
                    print(f"⚠️ 文件写入失败 {out_path}: {e}")

        processed_files += 1

    print(f"✅ Split & embed complete. 处理了 {processed_files} 个文件")

if __name__ == "__main__":
    main()
