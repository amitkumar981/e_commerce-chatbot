# importing libraries
from pathlib import Path
import os
import yaml

def _project_root() ->Path:
    return Path(__file__).resolve().parent.parent

def load_config(config_path: str | None = None) ->dict:
    env_path = os.getenv("CONFIG_PATH")
    if config_path is None:
        path = env_path or str(_project_root() / 'config' / 'config.yaml')
    
    path =  Path(path)
    if not path.is_absolute():
        path = _project_root() / path
    
    if not path.exists():
        raise FileNotFoundError(f"Config file {path} does not exist.")
    with open(path,'r',encoding='utf-8') as file:
        config = yaml.safe_load(file)
        return config or {}
    

    
    