# Archived leaderboard source

The nine Jekyll files in this directory are the reviewed personal-site draft. They are preserved byte-for-byte from the 2026-10-02 snapshot; standalone preview builds do not rewrite them.

From the repository root:

```bash
python3 tools/verify_repo.py
python3 tools/build_site.py
python3 -m http.server 8080 --directory dist --bind 127.0.0.1
```

Open `/benchmarks/qwen38-4090/`. See [site integration](../docs/site-integration.md) to copy the files into the personal website, and the [protocol](assets/benchmarks/qwen38-4090/README.md) before interpreting results or running the inference harnesses.
