# slang-shaders-metal

A utility to pre-compile RetroArch slang shader presets (`.slangp`) into OpenEmu-compatible compiled shader bundles (`.oecompiledshader`) targeted for Apple's Metal. Ships with a pre-built Apple Silicon `OpenEmuShaders.framework` and `oeshaders` CLI for convenience.

- **Inputs**: a checkout of `slang-shaders`
- **Outputs**: mirrored directory of compiled `.oecompiledshader` bundles plus logs
- **Runtime**: macOS (Apple Silicon recommended)

## Getting started

1. Clone this repository and ensure Python 3 is available.
2. Ensure `oeshaders` is executable (provided in this repo) or available in your `PATH`.
3. Run the compiler script pointing at your `slang-shaders` directory.

## Usage

```sh
python3 compile_shaders.py SRC_DIR [OUT_DIR] [TOOL] [METAL] [JOBS] [--no-filter|--filter=off|--filter|--filter=on|--filter=auto] [--help|-h]
```

- **SRC_DIR**: path to the `slang-shaders` root containing `.slangp` files
- **OUT_DIR**: output directory for compiled shaders (default: `./compiled_shaders`)
- **TOOL**: path to `oeshaders` CLI (default: `oeshaders` in PATH). Pass `.` or `./` to use default
- **METAL**: target Metal version string (default: `2.4`). On failures, script auto-retries with `2.3`
- **JOBS**: number of parallel compile jobs (default: CPU count)

### Options

- `--no-filter`, `--filter=off` (default)
  - Disables family filtering. Compiles all shader families.
- `--filter`, `--filter=on`, `--filter=auto`
  - Enables family filtering intended for mobile targets (iOS/tvOS). Skips heavy/incompatible families:
    - `motion-interpolation`, `stereoscopic-3d`, `hdr`, `gpu`
- `--help`, `-h`
  - Prints help and exits

### Outputs and logs

- Compiled shaders are written under `OUT_DIR`, mirroring the source tree, with the extension `.oecompiledshader`
- Per-file logs are written under `OUT_DIR/compile_logs/<relative>.log`
- A summary of failures is written to `OUT_DIR/failed.txt`
- Remaining failures after automatic retry with Metal 2.3 are listed in `OUT_DIR/failed.2.3.txt`

## Examples

- Default tool, defaults for output/Metal version, no filtering (default):

```sh
python3 compile_shaders.py ./slang-shaders
```

- Custom output dir, explicit tool and Metal version, 8 jobs:

```sh
python3 compile_shaders.py ./slang-shaders ./compiled_shaders ./oeshaders 2.4 8
```

- Filter for mobile targets (iOS/tvOS):

```sh
python3 compile_shaders.py ./slang-shaders ./compiled_shaders ./oeshaders 2.4 8 --filter
```

## Notes

- The included `OpenEmuShaders.framework` and `oeshaders` binary are provided for convenience. You can build them from the upstream project if preferred.
- By default, all shader families are compiled. For mobile (iOS/tvOS) targets, enable filtering with `--filter` to skip heavy/incompatible families.
- On failures, logs in `compile_logs` are the first place to inspect.
