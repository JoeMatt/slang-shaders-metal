# slang-shaders-metal

A repo with a script to pre-compile RetroArcjs slang-shaders to Metal useing OpenEMU's shader framework

This repo uses [OpenEMU-Shaders(https://github.com/OpenEmu/OpenEmu-Shaders), included as a pre-built Apple Silicon framework and binary, though these could be comiled yourself from the linked repo. It's included here pre-compiled since building can be tricky.

From there, we use the CLI tool in that repo to pre-compile the `glslang` shaders to a format `.oecompiledshader` which is a `zip` of the shader and resources for use in a Metal API pipelie.

A trimmed down version of the classes in [OpenEMU-Shaders(https://github.com/OpenEmu/OpenEmu-Shaders), can be used to parse and manage shaders included in your project.

Currently used by `DolphiniOS` fork by @JoeMatt

Example usage code is [here](https://github.com/Provenance-Emu/dolphin-ios-jitless/tree/brand175/master%2Bpatches/Source/iOS/App/Common/Swift/Shaders) as of time of publishing.


## How to use

Run `compile_shaders.py` with the parameters

- Directory of `slang-shaders` folder with glslang shaders.
- Output path
- Path to `oeshaders` binary (included)
- Metal Version API target (2.4 recommened, will fallback on failures)
- Number of shaders to compile in parallel


### TLDR;

```sh
python3 compile_shaders.py ./slang-shaders ./compiled_shaders ./oeshaders 2.4 8
```

