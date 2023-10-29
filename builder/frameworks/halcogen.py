from platformio.project.config import ProjectConfig

config = ProjectConfig.get_instance()

print(config.get("platformio", "src_dir"))