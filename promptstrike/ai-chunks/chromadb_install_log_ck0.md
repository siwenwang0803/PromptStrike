<!-- source: chromadb_install_log.txt idx:0 lines:88 -->

```txt
Collecting chromadb==0.4.10
  Downloading chromadb-0.4.10-py3-none-any.whl.metadata (7.0 kB)
Requirement already satisfied: requests>=2.28 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from chromadb==0.4.10) (2.32.4)
Collecting pydantic<2.0,>=1.9 (from chromadb==0.4.10)
  Downloading pydantic-1.10.22-cp313-cp313-macosx_10_13_x86_64.whl.metadata (154 kB)
Collecting chroma-hnswlib==0.7.3 (from chromadb==0.4.10)
  Using cached chroma-hnswlib-0.7.3.tar.gz (31 kB)
  Installing build dependencies: started
  Installing build dependencies: finished with status 'done'
  Getting requirements to build wheel: started
  Getting requirements to build wheel: finished with status 'done'
  Preparing metadata (pyproject.toml): started
  Preparing metadata (pyproject.toml): finished with status 'done'
Collecting fastapi<0.100.0,>=0.95.2 (from chromadb==0.4.10)
  Downloading fastapi-0.99.1-py3-none-any.whl.metadata (23 kB)
Requirement already satisfied: uvicorn>=0.18.3 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from uvicorn[standard]>=0.18.3->chromadb==0.4.10) (0.35.0)
Requirement already satisfied: posthog>=2.4.0 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from chromadb==0.4.10) (6.0.2)
Requirement already satisfied: typing-extensions>=4.5.0 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from chromadb==0.4.10) (4.14.0)
Requirement already satisfied: pulsar-client>=3.1.0 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from chromadb==0.4.10) (3.7.0)
Requirement already satisfied: onnxruntime>=1.14.1 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from chromadb==0.4.10) (1.22.0)
Requirement already satisfied: tokenizers>=0.13.2 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from chromadb==0.4.10) (0.21.2)
Requirement already satisfied: pypika>=0.48.9 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from chromadb==0.4.10) (0.48.9)
Requirement already satisfied: tqdm>=4.65.0 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from chromadb==0.4.10) (4.67.1)
Requirement already satisfied: overrides>=7.3.1 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from chromadb==0.4.10) (7.7.0)
Requirement already satisfied: importlib-resources in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from chromadb==0.4.10) (6.5.2)
Requirement already satisfied: bcrypt>=4.0.1 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from chromadb==0.4.10) (4.3.0)
Requirement already satisfied: numpy>=1.22.5 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from chromadb==0.4.10) (2.3.1)
Collecting starlette<0.28.0,>=0.27.0 (from fastapi<0.100.0,>=0.95.2->chromadb==0.4.10)
  Downloading starlette-0.27.0-py3-none-any.whl.metadata (5.8 kB)
Requirement already satisfied: anyio<5,>=3.4.0 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from starlette<0.28.0,>=0.27.0->fastapi<0.100.0,>=0.95.2->chromadb==0.4.10) (4.9.0)
Requirement already satisfied: idna>=2.8 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from anyio<5,>=3.4.0->starlette<0.28.0,>=0.27.0->fastapi<0.100.0,>=0.95.2->chromadb==0.4.10) (3.10)
Requirement already satisfied: sniffio>=1.1 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from anyio<5,>=3.4.0->starlette<0.28.0,>=0.27.0->fastapi<0.100.0,>=0.95.2->chromadb==0.4.10) (1.3.1)
Requirement already satisfied: coloredlogs in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from onnxruntime>=1.14.1->chromadb==0.4.10) (15.0.1)
Requirement already satisfied: flatbuffers in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from onnxruntime>=1.14.1->chromadb==0.4.10) (25.2.10)
Requirement already satisfied: packaging in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from onnxruntime>=1.14.1->chromadb==0.4.10) (25.0)
Requirement already satisfied: protobuf in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from onnxruntime>=1.14.1->chromadb==0.4.10) (5.29.5)
Requirement already satisfied: sympy in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from onnxruntime>=1.14.1->chromadb==0.4.10) (1.14.0)
Requirement already satisfied: six>=1.5 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from posthog>=2.4.0->chromadb==0.4.10) (1.17.0)
Requirement already satisfied: python-dateutil>=2.2 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from posthog>=2.4.0->chromadb==0.4.10) (2.9.0.post0)
Requirement already satisfied: backoff>=1.10.0 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from posthog>=2.4.0->chromadb==0.4.10) (2.2.1)
Requirement already satisfied: distro>=1.5.0 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from posthog>=2.4.0->chromadb==0.4.10) (1.9.0)
Requirement already satisfied: charset_normalizer<4,>=2 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from requests>=2.28->chromadb==0.4.10) (3.4.2)
Requirement already satisfied: urllib3<3,>=1.21.1 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from requests>=2.28->chromadb==0.4.10) (2.5.0)
Requirement already satisfied: certifi>=2017.4.17 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from requests>=2.28->chromadb==0.4.10) (2025.6.15)
Requirement already satisfied: huggingface-hub<1.0,>=0.16.4 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from tokenizers>=0.13.2->chromadb==0.4.10) (0.33.2)
Requirement already satisfied: filelock in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from huggingface-hub<1.0,>=0.16.4->tokenizers>=0.13.2->chromadb==0.4.10) (3.18.0)
Requirement already satisfied: fsspec>=2023.5.0 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from huggingface-hub<1.0,>=0.16.4->tokenizers>=0.13.2->chromadb==0.4.10) (2025.5.1)
Requirement already satisfied: pyyaml>=5.1 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from huggingface-hub<1.0,>=0.16.4->tokenizers>=0.13.2->chromadb==0.4.10) (6.0.2)
Requirement already satisfied: hf-xet<2.0.0,>=1.1.2 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from huggingface-hub<1.0,>=0.16.4->tokenizers>=0.13.2->chromadb==0.4.10) (1.1.5)
Requirement already satisfied: click>=7.0 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from uvicorn>=0.18.3->uvicorn[standard]>=0.18.3->chromadb==0.4.10) (8.2.1)
Requirement already satisfied: h11>=0.8 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from uvicorn>=0.18.3->uvicorn[standard]>=0.18.3->chromadb==0.4.10) (0.16.0)
Requirement already satisfied: httptools>=0.6.3 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from uvicorn[standard]>=0.18.3->chromadb==0.4.10) (0.6.4)
Requirement already satisfied: python-dotenv>=0.13 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from uvicorn[standard]>=0.18.3->chromadb==0.4.10) (1.1.1)
Requirement already satisfied: uvloop>=0.15.1 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from uvicorn[standard]>=0.18.3->chromadb==0.4.10) (0.21.0)
Requirement already satisfied: watchfiles>=0.13 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from uvicorn[standard]>=0.18.3->chromadb==0.4.10) (1.1.0)
Requirement already satisfied: websockets>=10.4 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from uvicorn[standard]>=0.18.3->chromadb==0.4.10) (15.0.1)
Requirement already satisfied: humanfriendly>=9.1 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from coloredlogs->onnxruntime>=1.14.1->chromadb==0.4.10) (10.0)
Requirement already satisfied: mpmath<1.4,>=1.1.0 in /Users/siwenwang/PromptStrike/.venv/lib/python3.13/site-packages (from sympy->onnxruntime>=1.14.1->chromadb==0.4.10) (1.3.0)
Downloading chromadb-0.4.10-py3-none-any.whl (422 kB)
Downloading fastapi-0.99.1-py3-none-any.whl (58 kB)
Downloading pydantic-1.10.22-cp313-cp313-macosx_10_13_x86_64.whl (2.8 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.8/2.8 MB 40.0 MB/s eta 0:00:00
Downloading starlette-0.27.0-py3-none-any.whl (66 kB)
Building wheels for collected packages: chroma-hnswlib
  Building wheel for chroma-hnswlib (pyproject.toml): started
  Building wheel for chroma-hnswlib (pyproject.toml): finished with status 'error'
  error: subprocess-exited-with-error
  
  × Building wheel for chroma-hnswlib (pyproject.toml) did not run successfully.
  │ exit code: 1
  ╰─> [11 lines of output]
      running bdist_wheel
      running build
      running build_ext
      creating var/folders/gr/681nsy212ds2w8g0r310fcf00000gn/T
      clang++ -fno-strict-overflow -Wsign-compare -Wunreachable-code -fno-common -dynamic -DNDEBUG -g -O3 -Wall -arch arm64 -arch x86_64 -I/Users/siwenwang/PromptStrike/.venv/include -I/Library/Frameworks/Python.framework/Versions/3.13/include/python3.13 -c /var/folders/gr/681nsy212ds2w8g0r310fcf00000gn/T/tmp8a_48ll6.cpp -o var/folders/gr/681nsy212ds2w8g0r310fcf00000gn/T/tmp8a_48ll6.o -std=c++14
      clang++ -fno-strict-overflow -Wsign-compare -Wunreachable-code -fno-common -dynamic -DNDEBUG -g -O3 -Wall -arch arm64 -arch x86_64 -I/Users/siwenwang/PromptStrike/.venv/include -I/Library/Frameworks/Python.framework/Versions/3.13/include/python3.13 -c /var/folders/gr/681nsy212ds2w8g0r310fcf00000gn/T/tmpkvmatppq.cpp -o var/folders/gr/681nsy212ds2w8g0r310fcf00000gn/T/tmpkvmatppq.o -fvisibility=hidden
      building 'hnswlib' extension
      creating build/temp.macosx-10.13-universal2-cpython-313/python_bindings
      clang++ -fno-strict-overflow -Wsign-compare -Wunreachable-code -fno-common -dynamic -DNDEBUG -g -O3 -Wall -arch arm64 -arch x86_64 -I/private/var/folders/gr/681nsy212ds2w8g0r310fcf00000gn/T/pip-build-env-likyt4qk/overlay/lib/python3.13/site-packages/pybind11/include -I/private/var/folders/gr/681nsy212ds2w8g0r310fcf00000gn/T/pip-build-env-likyt4qk/overlay/lib/python3.13/site-packages/numpy/_core/include -I./hnswlib/ -I/Users/siwenwang/PromptStrike/.venv/include -I/Library/Frameworks/Python.framework/Versions/3.13/include/python3.13 -c ./python_bindings/bindings.cpp -o build/temp.macosx-10.13-universal2-cpython-313/python_bindings/bindings.o -O3 -march=native -stdlib=libc++ -mmacosx-version-min=10.7 -DVERSION_INFO=\"0.7.3\" -std=c++14 -fvisibility=hidden
      clang: error: the clang compiler does not support '-march=native'
      error: command '/usr/bin/clang++' failed with exit code 1
      [end of output]
  
  note: This error originates from a subprocess, and is likely not a problem with pip.
  ERROR: Failed building wheel for chroma-hnswlib
Failed to build chroma-hnswlib
ERROR: Failed to build installable wheels for some pyproject.toml based projects (chroma-hnswlib)
```