from platformio.project.config import ProjectConfig

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
config = ProjectConfig.get_instance()

print(config.get("platformio", "src_dir"))
