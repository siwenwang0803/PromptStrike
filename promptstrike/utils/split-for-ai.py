#!/usr/bin/env python
"""
split-for-ai.py --repo . --max-lines 800 --min-lines 50 --db .chroma
"""
import argparse
import os
import shutil
import pathlib
from typing import List, Set
from tqdm import tqdm
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 显式禁用代理相关环境变量
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""
os.environ["NO_PROXY"] = "*"
os.environ["OPENAI_PROXY"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""

EMB_SIZE = 1536  # openai ada-002

def chunk_lines(lines: List[str], max_lines: int = 800, min_lines: int = 50):
    """Split lines into chunks, ensuring each chunk meets minimum size requirement."""
    for i in range(0, len(lines), max_lines):
        chunk = lines[i : i + max_lines]
        if len(chunk) >= min_lines:
            yield chunk

def should_skip_file(path: pathlib.Path, skip_dirs: Set[str], skip_suffixes: Set[str]) -> bool:
    """Check if file should be skipped based on path or extension."""
    if any(part in skip_dirs for part in path.parts) or '.venv' in str(path):
        return True
    if path.suffix.lower() in skip_suffixes:
        return True
    skip_names = {'package-lock.json', 'yarn.lock', 'Pipfile.lock', 'poetry.lock',
                  '.DS_Store', 'Thumbs.db', '.gitignore', '.gitattributes'}
    if path.name in skip_names:
        return True
    try:
        if path.stat().st_size > 10 * 1024 * 1024:  # 10MB
            return True
    except (OSError, FileNotFoundError):
        return True
    return False

def is_text_file(path: pathlib.Path) -> bool:
    """Check if file is likely a text file."""
    text_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss', '.sass',
                       '.md', '.txt', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',
                       '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd',
                       '.sql', '.graphql', '.gql', '.xml', '.svg', '.csv', '.tsv',
                       '.dockerfile', '.gitignore', '.env', '.editorconfig',
                       '.c', '.cpp', '.h', '.hpp', '.java', '.kt', '.swift', '.go', '.rs',
                       '.php', '.rb', '.pl', '.r', '.scala', '.clj', '.hs', '.elm',
                       '.vue', '.svelte', '.astro', '.prisma'}
    if path.suffix.lower() in text_extensions:
        return True
    if not path.suffix and path.name not in {'.DS_Store', 'Thumbs.db'}:
        try:
            with open(path, 'rb') as f:
                chunk = f.read(1024)
                printable = sum(1 for b in chunk if 32 <= b <= 126 or b in (9, 10, 13))
                return len(chunk) == 0 or printable / len(chunk) > 0.95
        except (OSError, FileNotFoundError):
            return False
    return False

def migrate_or_clear_db(db_path: pathlib.Path):
    """Check for existing DB and attempt migration or clear if incompatible."""
    if db_path.exists():
        logger.warning(f"Existing .chroma database found at {db_path}. Attempting to clear for migration.")
        try:
            shutil.rmtree(db_path)
            logger.info(f"Cleared old database at {db_path} to ensure compatibility with new architecture.")
        except Exception as e:
            logger.error(f"Failed to clear old database: {e}")
            raise

def main():
    ap = argparse.ArgumentParser(description="Split source files for AI embedding")
    ap.add_argument("--repo", default=".", help="Repository path")
    ap.add_argument("--max-lines", type=int, default=800, help="Maximum lines per chunk")
    ap.add_argument("--min-lines", type=int, default=50, help="Minimum lines per chunk")
    ap.add_argument("--db", default=".chroma", help="ChromaDB path")
    ap.add_argument("--collection", default="promptstrike", help="Collection name")
    ap.add_argument("--dry_run", action="store_true", help="Show what would be processed without doing it")
    args = ap.parse_args()

    if args.min_lines >= args.max_lines:
        logger.error("Error: min-lines must be less than max-lines")
        return 1

    repo = pathlib.Path(args.repo).resolve()
    if not repo.exists():
        logger.error(f"Error: Repository path {repo} does not exist")
        return 1

    skip_suffixes = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.ico', '.svg',
                     '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                     '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar',
                     '.exe', '.dll', '.so', '.dylib', '.bin',
                     '.lock', '.pyc', '.pyo', '.pyd', '.class',
                     '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac',
                     '.ttf', '.otf', '.woff', '.woff2', '.eot'}
    skip_dirs = {".git", ".svn", ".hg", ".venv", "venv", "env", "__pycache__", ".pytest_cache",
                 "node_modules", ".npm", ".yarn", ".chroma", "ai-chunks",
                 "target", "build", "dist", "out", ".idea", ".vscode", ".vs",
                 "vendor", "third_party"}

    if args.dry_run:
        logger.info("🔍 Dry run mode - showing what would be processed...")

    if not args.dry_run:
        db_path = pathlib.Path(args.db)
        try:
            migrate_or_clear_db(db_path)
            # 为 chromadb==0.4.10 创建简单的 Settings，只传入支持的参数
            settings = Settings(
                anonymized_telemetry=False,
                persist_directory=args.db
            )
            chroma_client = chromadb.Client(settings=settings)
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.error("Error: OPENAI_API_KEY environment variable not set")
                return 1
            
            # 检查 API key 格式
            if api_key == "***" or len(api_key) < 10 or not api_key.startswith("sk-"):
                logger.error(f"Error: OPENAI_API_KEY appears to be invalid. Got: {api_key[:10]}...")
                logger.error("Please ensure OPENAI_API_KEY is properly set in GitHub Secrets")
                return 1
            
            # 使用兼容的 embedding function
            embed_fn = embedding_functions.OpenAIEmbeddingFunction(
                api_key=api_key,
                model_name="text-embedding-ada-002"  # 使用兼容的模型名称
            )
            
            try:
                # 获取现有 collection，注意要传入 embedding_function
                coll = chroma_client.get_collection(
                    name=args.collection,
                    embedding_function=embed_fn
                )
                logger.info(f"✅ Using existing collection: {args.collection}")
            except Exception:
                coll = chroma_client.create_collection(
                    name=args.collection,
                    embedding_function=embed_fn
                )
                logger.info(f"✅ Created new collection: {args.collection}")
        except Exception as e:
            logger.error(f"Error setting up ChromaDB: {e}")
            import traceback
            traceback.print_exc()
            return 1

    processed_files = 0
    skipped_files = 0
    total_chunks = 0
    all_files = [p for p in repo.rglob("*") if p.is_file()]

    for path in tqdm(all_files, desc="Processing files"):
        if should_skip_file(path, skip_dirs, skip_suffixes):
            skipped_files += 1
            continue
        if not is_text_file(path):
            skipped_files += 1
            continue
        rel = path.relative_to(repo)
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception as e:
            logger.warning(f"Skipping file {rel}: {e}")
            skipped_files += 1
            continue
        if len(text) < args.min_lines:
            skipped_files += 1
            continue

        if len(text) <= args.max_lines:
            chunks = [text] if len(text) >= args.min_lines else []
        else:
            chunks = list(chunk_lines(text, args.max_lines, args.min_lines))

        if args.dry_run:
            if chunks:
                logger.info(f"📄 Would process: {rel} ({len(text)} lines → {len(chunks)} chunks)")
                total_chunks += len(chunks)
            continue

        for idx, chunk in enumerate(chunks):
            doc_id = f"{rel}::ck{idx}"
            content = "\n".join(chunk)
            try:
                coll.add(
                    ids=[doc_id],
                    documents=[content],
                    metadatas=[{"path": str(rel), "idx": idx, "lines": len(chunk)}]
                )
            except Exception as e:
                logger.error(f"ChromaDB add failed {doc_id}: {e}")
                continue

            out_dir = repo / "ai-chunks" / rel.parent
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{rel.stem}_ck{idx}.md"
            try:
                file_ext = path.suffix[1:] if path.suffix else 'text'
                out_path.write_text(
                    f"<!-- source: {rel} idx:{idx} lines:{len(chunk)} -->\n\n```{file_ext}\n{content}\n```",
                    encoding="utf-8"
                )
            except Exception as e:
                logger.error(f"File write failed {out_path}: {e}")
            total_chunks += 1

        processed_files += 1

    if args.dry_run:
        logger.info(f"\n📊 Dry run summary:")
        logger.info(f"   Files that would be processed: {processed_files}")
        logger.info(f"   Total chunks that would be created: {total_chunks}")
        logger.info(f"   Files that would be skipped: {skipped_files}")
    else:
        logger.info(f"\n✅ Split & embed complete:")
        logger.info(f"   Processed files: {processed_files}")
        logger.info(f"   Total chunks created: {total_chunks}")
        logger.info(f"   Skipped files: {skipped_files}")
        logger.info(f"   Database: {args.db}")
        logger.info(f"   Collection: {args.collection}")

    return 0

if __name__ == "__main__":
    exit(main())



