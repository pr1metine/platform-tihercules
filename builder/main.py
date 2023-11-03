"""
    Builder for Texas Instruments Cortex-R5 based microcontrollers
"""

from os.path import join

from SCons.Script import (
    COMMAND_LINE_TARGETS,
    AlwaysBuild,
    Builder,
    Default,
    DefaultEnvironment,
)

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()

ccxmls = join(platform.get_dir() or "", "misc", "ccxml")

env.Replace(
    AR="arm-none-eabi-ar",
    AS="arm-none-eabi-as",
    CC="arm-none-eabi-gcc",
    CXX="arm-none-eabi-g++",
    GDB="arm-none-eabi-gdb",
    OBJCOPY="arm-none-eabi-objcopy",
    RANLIB="arm-none-eabi-ranlib",
    SIZETOOL="arm-none-eabi-size",
    ARFLAGS=["rc"],
    SIZEPROGREGEXP=r"^(?:\.text|\.data|\.rodata|\.text.align|\.ARM.exidx)\s+(\d+).*",
    SIZEDATAREGEXP=r"^(?:\.data|\.bss|\.noinit)\s+(\d+).*",
    SIZECHECKCMD="$SIZETOOL -A -d $SOURCES",
    SIZEPRINTCMD="$SIZETOOL -B -d $SOURCES",
    PROGSUFFIX=".elf",
)

# Allow user to override via pre:script
if env.get("PROGNAME", "program") == "program":
    env.Replace(PROGNAME="firmware")

machine_flags = []

env.Append(
    ASFLAGS=machine_flags,
    ASPPFLAGS=[
        "-x",
        "assembler-with-cpp",
    ],
    CCFLAGS=machine_flags
    + [
        "-Os",  # optimize for size
        "-ffunction-sections",  # place each function in its own section
        "-fdata-sections",
        "-Wall",
        "-nostdlib",
    ],
    CFLAGS=["-std=gnu11"],
    CXXFLAGS=[
        "-fno-rtti",
        "-fno-exceptions",
        "-fno-threadsafe-statics",
        "-std=gnu++11",
    ],
    LINKFLAGS=machine_flags + ["-Os", "-nostartfiles", "-nostdlib"],
    LIBS=["c", "gcc", "m"],
    BUILDERS=dict(
        ElfToBin=Builder(
            action=env.VerboseAction(
                " ".join(["$OBJCOPY", "-O", "binary", "$SOURCES", "$TARGET"]),
                "Building $TARGET",
            ),
            suffix=".bin",
        ),
        ElfToHex=Builder(
            action=env.VerboseAction(" ".join([
                "$OBJCOPY",
                "-O",
                "ihex",
                "-R",
                ".eeprom",
                "$SOURCES",
                "$TARGET"
            ]), "Building $TARGET"),
            suffix=".hex"
        )
    ),
)

if "BOARD" in env:
    args = ["-mcpu=%s" % board.get("build.cpu"), "-mfpu=%s" % board.get("build.fpu")]
    env.Append(
        ASFLAGS=args,
        CCFLAGS=args,
        LINKFLAGS=args,
    )

#
# Target: Build executable and linkable firmware
#

target_elf = None
if "nobuild" in COMMAND_LINE_TARGETS:
    target_elf = join("$BUILD_DIR", "${PROGNAME}.elf")
    target_firm = join("$BUILD_DIR", "${PROGNAME}.bin")
else:
    target_elf = env.BuildProgram()
    target_firm = env.ElfToHex(join("$BUILD_DIR", "${PROGNAME}"), target_elf)
    env.Depends(target_firm, "checkprogsize")

AlwaysBuild(env.Alias("nobuild", target_firm))
target_buildprog = env.Alias("buildprog", target_firm, target_firm)

#
# Target: Print binary size
#

target_size = env.Alias(
    "size", target_elf, env.VerboseAction("$SIZEPRINTCMD", "Calculating size $SOURCE")
)
AlwaysBuild(target_size)

#
# Target: Flash target
#

upload_protocol = env.subst("$UPLOAD_PROTOCOL")
debug_tools = board.get("debug.tools", {})
upload_source = target_firm
upload_actions = []

if upload_protocol == "dslite":
    env.Replace(
        # UPLOADER=join(
        #     platform.get_package_dir("tool-dslite") or "", // TODO: Remove dependency from user installed dslite
        #     "DebugServer",
        #     "bin",
        #     "DSLite"
        # ),
        UPLOADER="dslite",
        UPLOADERFLAGS=[
            # "load", "-c",
            # join(ccxmls, f'${board.get("build.variant") or "RM57L8xx"}.ccxml'),
            "-c",
            join(ccxmls, 'RM57L8xx.ccxml'),
            "-u",
            "-f"
        ],
        UPLOADCMD="$UPLOADER $UPLOADERFLAGS $SOURCES"
    )
    upload_source = target_firm
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

target_upload = env.Alias("upload", upload_source, upload_actions)
AlwaysBuild(target_upload)

#
# Target: Default targets
#

Default([target_buildprog, target_size])
