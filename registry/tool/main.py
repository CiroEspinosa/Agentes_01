import threading
import yaml
from typing import Optional, List
from logging import Logger

import uvicorn
from pathlib import Path

from fastapi import FastAPI, HTTPException, status

from factory import web_factory
from model.vo import ToolVO
from utils import logging_config

app: FastAPI = web_factory.create_app()

logger: Logger = logging_config.get_logger(__name__)


@app.get("/tools")
def tools() -> list[ToolVO]:
    tool_list: list[ToolVO] = []
    yaml_files: list[Path] = _list_yaml_files()
    # Iterate over YAML files list
    for yaml_file in yaml_files:
        try:
            with yaml_file.open("r") as file:
                content = file.read()
                data_dict = yaml.safe_load(content)
                if "swagger" in data_dict:
                    tool_vo = ToolVO.from_dict(data_dict)
                    tool_list.append(tool_vo)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {yaml_file}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while processing file {yaml_file}: {e}")
    return tool_list


@app.get("/tools/{identifier}")
def tool(identifier: str) -> Optional[ToolVO]:
    tool_vo: Optional[ToolVO] = None
    yaml_files: list[Path] = _list_yaml_files()
    i: int = 0
    tool_found: bool = False
    # Iterate over each YAML file until agent YAML is found
    while i < len(yaml_files) and not tool_found:
        try:
            with yaml_files[i].open("r") as file:
                content = file.read()
                data_dict = yaml.safe_load(content)
                if "swagger" in data_dict:
                    if data_dict["id"] == identifier:
                        tool_vo = ToolVO.from_dict(data_dict)
                        tool_found = True

        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {yaml_files[i]}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while processing file {yaml_files[i]}: {e}")
        i += 1
    if not tool_found:
        # If the tool is not found, raise a 404 error
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool with id '{identifier}' not found"
        )
    return tool_vo


@app.get("/health")
def health() -> dict:
    return {
        "registry": "tool-registry",
        "thread": f"{threading.current_thread().name}"
    }


def _list_yaml_files() -> list[Path]:
    # Specify the directory
    directory = Path("./")

    # Recursively list all YAML files
    yaml_files = directory.rglob('*.yaml')
    yaml_files = list(yaml_files) + list(directory.rglob('*.yml'))
    return yaml_files


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7001)
