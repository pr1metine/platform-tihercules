from platformio.project.config import ProjectConfig
from os.path import join, isfile
from SCons.Script import DefaultEnvironment
import sys

env = DefaultEnvironment()
config = ProjectConfig.get_instance()

src_dir = config.get("platformio", "src_dir")
link_script = join(src_dir, "HL_sys_link.ld")

if not isfile(link_script):
    sys.stderr.write(f"No HALCOGEN linker file found {link_script}! Build will most likely fail")

env.Replace(
    LDSCRIPT_PATH=link_script
)
env.Append(LINKFLAGS=["--specs=nosys.specs", "--specs=nano.specs"])