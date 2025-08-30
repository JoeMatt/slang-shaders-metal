#!/usr/bin/env python3
import concurrent.futures as cf, os, sys, subprocess, pathlib, multiprocessing


def print_help():
    print(
        """
Usage: compile_shaders.py SRC_DIR [OUT_DIR] [TOOL] [METAL] [JOBS] [--no-filter|--filter=off|--filter|--filter=on|--filter=auto] [--help|-h]

Pre-compiles RetroArch slang shader presets (.slangp) into OpenEmu-compatible compiled shader bundles (.oecompiledshader) for Metal.

Positional arguments:
  SRC_DIR     Path to the 'slang-shaders' root containing .slangp files
  OUT_DIR     Output directory for compiled shaders (default: ./compiled_shaders)
  TOOL        Path to the 'oeshaders' CLI (default: 'oeshaders' in PATH). Pass '.' or './' to use default
  METAL       Target Metal version string (default: 2.4). On failures, automatically retries with 2.3
  JOBS        Number of parallel compile jobs (default: CPU count)

Options:
  --no-filter, --filter=off   Disable family filtering; include all shader families (default)
  --filter, --filter=on,
  --filter=auto               Enable family filtering (intended for mobile targets such as iOS/tvOS). Skips heavy/incompatible families:
                              motion-interpolation, stereoscopic-3d, hdr, gpu
  --help, -h                  Show this help and exit

Outputs and logs:
  - Compiled shaders written under OUT_DIR mirroring source tree, with extension .oecompiledshader
  - Per-file compile logs written under OUT_DIR/compile_logs/<relative>.log
  - Failures summarized in OUT_DIR/failed.txt; retried with Metal 2.3 and remaining failures in failed.2.3.txt
""".strip()
    )


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
    # Help requested anywhere
    if any(a in ("--help", "-h") for a in sys.argv[1:]):
        print_help(); sys.exit(0)
    if len(sys.argv) < 2:
        print_help(); sys.exit(1)

    src = os.path.abspath(sys.argv[1])

    # Separate positional values and options appearing anywhere after SRC_DIR
    args_after_src = sys.argv[2:]
    pos = [a for a in args_after_src if not a.startswith("--")]
    opts = [a for a in args_after_src if a.startswith("--")]

    out = os.path.abspath(pos[0]) if len(pos) > 0 else os.path.abspath("compiled_shaders")
    tool = pos[1] if len(pos) > 1 and pos[1] not in ('.', './') else "oeshaders"
    metal = pos[2] if len(pos) > 2 else "2.4"
    jobs = int(pos[3]) if len(pos) > 3 else multiprocessing.cpu_count()

    # Parse flags (filter is OFF by default)
    filter_on = False
    for a in opts:
        if a in ("--no-filter", "--filter=off"):
            filter_on = False
        elif a in ("--filter=on", "--filter", "--filter=auto"):
            filter_on = True

    logroot = os.path.join(out, "compile_logs")
    os.makedirs(out, exist_ok=True); os.makedirs(logroot, exist_ok=True)
    fails_path = os.path.join(out, "failed.txt")

    # Families known to be heavy/incompatible for mobile targets; skipped when filter is enabled
    exclude = {"motion-interpolation","stereoscopic-3d","hdr","gpu"} if filter_on else set()

    files = []
    for root, dirs, filenames in os.walk(src):
        # prune excludes when filter is enabled
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
