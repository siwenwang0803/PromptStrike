#!/usr/bin/env python
"""
split-for-ai.py --repo . --max-lines 800 --min-lines 50 --db .chroma
"""
import argparse
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"  # 禁用ChromaDB遥测
os.environ["CHROMA_DB_IMPL"] = "duckdb+parquet"
import argparse
import pathlib
from typing import List, Set
from tqdm import tqdm
import chromadb
from chromadb.utils import embedding_functions

EMB_SIZE = 1536  # openai ada-002

def chunk_lines(lines: List[str], max_lines: int = 800, min_lines: int = 50):
    """Split lines into chunks, ensuring each chunk meets minimum size requirement."""
    for i in range(0, len(lines), max_lines):
        chunk = lines[i : i + max_lines]
        if len(chunk) >= min_lines:
            yield chunk

def should_skip_file(path: pathlib.Path, skip_dirs: Set[str], skip_suffixes: Set[str]) -> bool:
    """Check if file should be skipped based on path or extension."""
    # Skip based on directory parts
    if any(part in skip_dirs for part in path.parts) or '.venv' in str(path):
        return True
    
    # Skip based on file extension
    if path.suffix.lower() in skip_suffixes:
        return True
        
    # Skip common lockfiles and config files that shouldn't be embedded
    skip_names = {
        'package-lock.json', 'yarn.lock', 'Pipfile.lock', 'poetry.lock',
        '.DS_Store', 'Thumbs.db', '.gitignore', '.gitattributes'
    }
    if path.name in skip_names:
        return True
        
    # Skip very large files (>10MB) to avoid memory issues
    try:
        if path.stat().st_size > 10 * 1024 * 1024:  # 10MB
            return True
    except (OSError, FileNotFoundError):
        return True
        
    return False

def is_text_file(path: pathlib.Path) -> bool:
    """Check if file is likely a text file."""
    text_extensions = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss', '.sass',
        '.md', '.txt', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',
        '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd',
        '.sql', '.graphql', '.gql', '.xml', '.svg', '.csv', '.tsv',
        '.dockerfile', '.gitignore', '.env', '.editorconfig',
        '.c', '.cpp', '.h', '.hpp', '.java', '.kt', '.swift', '.go', '.rs',
        '.php', '.rb', '.pl', '.r', '.scala', '.clj', '.hs', '.elm',
        '.vue', '.svelte', '.astro', '.prisma'
    }
    
    # Check by extension
    if path.suffix.lower() in text_extensions:
        return True
    
    # Check files without extension (often scripts or config files)
    if not path.suffix and path.name not in {'.DS_Store', 'Thumbs.db'}:
        try:
            # Try to read first 1024 bytes to check if it's text
            with open(path, 'rb') as f:
                chunk = f.read(1024)
                # Simple heuristic: if more than 95% are printable ASCII, likely text
                printable = sum(1 for b in chunk if 32 <= b <= 126 or b in (9, 10, 13))
                return len(chunk) == 0 or printable / len(chunk) > 0.95
        except (OSError, FileNotFoundError):
            return False
    
    return False

def main():
    ap = argparse.ArgumentParser(description="Split source files for AI embedding")
    ap.add_argument("--repo", default=".", help="Repository path")
    ap.add_argument("--max-lines", type=int, default=800, help="Maximum lines per chunk")
    ap.add_argument("--min-lines", type=int, default=50, help="Minimum lines per chunk")
    ap.add_argument("--db", default=".chroma", help="ChromaDB path")
    ap.add_argument("--collection", default="promptstrike", help="Collection name")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be processed without doing it")
    args = ap.parse_args()

    if args.min_lines >= args.max_lines:
        print("❌ Error: min-lines must be less than max-lines")
        return 1

    repo = pathlib.Path(args.repo).resolve()
    
    if not repo.exists():
        print(f"❌ Error: Repository path {repo} does not exist")
        return 1
    
    # Extended file type and directory exclusion
    skip_suffixes = {
        # Images
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.ico', '.svg',
        # Documents  
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        # Archives
        '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar',
        # Binaries
        '.exe', '.dll', '.so', '.dylib', '.bin',
        # Locks and caches
        '.lock', '.pyc', '.pyo', '.pyd', '.class',
        # Media
        '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac',
        # Fonts
        '.ttf', '.otf', '.woff', '.woff2', '.eot'
    }
    
    skip_dirs = {
        ".git", ".svn", ".hg",  # VCS
        ".venv", "venv", "env", "__pycache__", ".pytest_cache",  # Python
        "node_modules", ".npm", ".yarn",  # JavaScript
        ".chroma", "ai-chunks",  # This tool's output
        "target", "build", "dist", "out",  # Build outputs
        ".idea", ".vscode", ".vs",  # IDEs
        "vendor", "third_party"  # Dependencies
    }

    if args.dry_run:
        print("🔍 Dry run mode - showing what would be processed...")
        
    # Create ChromaDB client (only if not dry run)
    if not args.dry_run:
        try:
            chroma_client = chromadb.PersistentClient(path=args.db)
            
            # Create embedding function
            if not os.getenv("OPENAI_API_KEY"):
                print("❌ Error: OPENAI_API_KEY environment variable not set")
                return 1
                
            embed_fn = embedding_functions.OpenAIEmbeddingFunction(
                api_key=os.getenv("OPENAI_API_KEY"),
                model_name="text-embedding-3-small",
            )
            
            # Get or create collection
            try:
                coll = chroma_client.get_collection(args.collection)
                print(f"✅ Using existing collection: {args.collection}")
            except:
                coll = chroma_client.create_collection(
                    name=args.collection, 
                    embedding_function=embed_fn
                )
                print(f"✅ Created new collection: {args.collection}")
        except Exception as e:
            print(f"❌ Error setting up ChromaDB: {e}")
            return 1

    processed_files = 0
    skipped_files = 0
    total_chunks = 0
    
    # Collect all files first for better progress tracking
    all_files = [p for p in repo.rglob("*") if p.is_file()]
    
    for path in tqdm(all_files, desc="Processing files"):
        # Apply all skip filters
        if should_skip_file(path, skip_dirs, skip_suffixes):
            skipped_files += 1
            continue
            
        # Check if it's a text file
        if not is_text_file(path):
            skipped_files += 1
            continue
            
        rel = path.relative_to(repo)
        
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception as e:
            if not args.dry_run:
                print(f"⚠️ Skipping file {rel}: {e}")
            skipped_files += 1
            continue
            
        if len(text) < args.min_lines:
            skipped_files += 1
            continue

        # Chunk processing
        if len(text) <= args.max_lines:
            chunks = [text] if len(text) >= args.min_lines else []
        else:
            chunks = list(chunk_lines(text, args.max_lines, args.min_lines))

        if args.dry_run:
            if chunks:
                print(f"📄 Would process: {rel} ({len(text)} lines → {len(chunks)} chunks)")
                total_chunks += len(chunks)
            continue

        for idx, chunk in enumerate(chunks):
            doc_id = f"{rel}::ck{idx}"
            content = "\n".join(chunk)
            
            # Add to ChromaDB
            try:
                coll.add(
                    ids=[doc_id], 
                    documents=[content], 
                    metadatas=[{"path": str(rel), "idx": idx, "lines": len(chunk)}]
                )
            except Exception as e:
                print(f"⚠️ ChromaDB add failed {doc_id}: {e}")
                

            # Save to file for inspection
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
                print(f"⚠️ File write failed {out_path}: {e}")
            
            total_chunks += 1

        processed_files += 1

    # Summary
    if args.dry_run:
        print(f"\n📊 Dry run summary:")
        print(f"   Files that would be processed: {processed_files}")
        print(f"   Total chunks that would be created: {total_chunks}")
        print(f"   Files that would be skipped: {skipped_files}")
    else:
        print(f"\n✅ Split & embed complete:")
        print(f"   Processed files: {processed_files}")
        print(f"   Total chunks created: {total_chunks}")
        print(f"   Skipped files: {skipped_files}")
        print(f"   Database: {args.db}")
        print(f"   Collection: {args.collection}")

    return 0

if __name__ == "__main__":
    exit(main())
