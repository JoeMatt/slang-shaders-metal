#!/usr/bin/env python3
import concurrent.futures as cf, os, sys, subprocess, pathlib, multiprocessing

def compile_one(args):
    f, src, out, tool, metal, logroot = args
    rel = os.path.relpath(f, src)
    dst_dir = os.path.join(out, os.path.dirname(rel))
    base = os.path.splitext(os.path.basename(rel))[0]
    dst_file = os.path.join(dst_dir, base + ".oecompiledshader")
    log_path = os.path.join(logroot, rel + ".log")
    os.makedirs(dst_dir, exist_ok=True)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    if os.path.exists(dst_file):
        return (rel, True, None)
    with open(log_path, "w") as logf:
        proc = subprocess.run([tool, "compile", f, dst_file, metal, "--disable-cache"], stdout=logf, stderr=subprocess.STDOUT)
        return (rel, proc.returncode == 0, log_path)

def main():
    if len(sys.argv) < 2:
        print("Usage: compile_shaders.py /path/to/slang-shaders [out] [tool] [metal] [jobs] [--no-filter|--filter=off]", file=sys.stderr); sys.exit(1)
    src = os.path.abspath(sys.argv[1])
    out = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.abspath("compiled_shaders")
    tool = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] not in ('.', './') else "oeshaders"
    metal = sys.argv[4] if len(sys.argv) > 4 else "2.4"
    jobs = int(sys.argv[5]) if len(sys.argv) > 5 and not sys.argv[5].startswith("--") else multiprocessing.cpu_count()

    # Parse extra flags (after positional args)
    filter_on = True
    extra = [a for a in sys.argv[6:] if a.startswith("--")] if len(sys.argv) > 6 else []
    for a in extra:
        if a in ("--no-filter", "--filter=off"):
            filter_on = False
        elif a in ("--filter=on", "--filter", "--filter=auto"):
            filter_on = True

    logroot = os.path.join(out, "compile_logs")
    os.makedirs(out, exist_ok=True); os.makedirs(logroot, exist_ok=True)
    fails_path = os.path.join(out, "failed.txt")

    # Families known to be heavy/incompatible for iOS/tvOS; skip by default unless --no-filter
    exclude = {"motion-interpolation","stereoscopic-3d","hdr","gpu"} if filter_on else set()

    files = []
    for root, dirs, filenames in os.walk(src):
        # prune excludes
        if exclude:
            dirs[:] = [d for d in dirs if d not in exclude]
        for name in filenames:
            if name.endswith(".slangp"):
                files.append(os.path.join(root, name))

    print(f"Source: {src}\nOutput: {out}\nTool: {tool} (Metal {metal})\nJobs: {jobs}\nFilter: {'on' if filter_on else 'off'}\n")
    tasks = [(f, src, out, tool, metal, logroot) for f in files]

    failed = []
    with cf.ThreadPoolExecutor(max_workers=jobs) as ex:
        for rel, ok, log_path in ex.map(compile_one, tasks):
            if ok:
                print(f"OK: {rel}")
            else:
                print(f"FAILED: {rel}")
                failed.append(rel)

    if failed:
        with open(fails_path, "w") as f: f.write("\n".join(f"FAILED: {rel}" for rel in failed))
        print(f"\nFailures logged in {fails_path} (see per-file logs under {logroot})")

        # Retry with Metal 2.3
        retry_fails = []
        retry_tasks = []
        for rel in failed:
            f = os.path.join(src, rel)
            retry_tasks.append((f, src, out, tool, "2.3", logroot))
        print("\nRetrying failed with Metal 2.3...\n")
        with cf.ThreadPoolExecutor(max_workers=jobs) as ex:
            for rel, ok, _ in ex.map(compile_one, retry_tasks):
                if not ok: retry_fails.append(rel)
        if retry_fails:
            with open(os.path.join(out, "failed.2.3.txt"), "w") as f: f.write("\n".join(retry_fails))

if __name__ == "__main__":
    main()
