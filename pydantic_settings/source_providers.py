import os
import warnings
from pathlib import Path
from typing import Any, Dict, Iterator, Mapping, Optional

from pydantic.typing import StrPath
from pydantic.utils import path_type

from .utils import DotenvType, SettingsError


class SecretSource(Mapping[str, Any]):
    def __init__(self, secrets_dir_path: Path) -> None:
        self.secrets_dir_path = secrets_dir_path
        self._valid_paths: Dict[str, Path] = {}
        for f in self.secrets_dir_path.iterdir():
            if f.is_file():
                self._valid_paths[f.name] = f

    def __getitem__(self, key: str) -> Any:
        file_path = self._valid_paths.get(key)
        if file_path:
            return file_path.read_text().strip()

    def __iter__(self) -> Iterator[str]:
        yield from self._valid_paths.keys()

    def __len__(self) -> int:
        return len(self._valid_paths)


def secret_source_provider(secrets_dir_path: Optional[StrPath] = None) -> Mapping[str, Any]:
    """Returns dictionary with filename as key and the content as values for all
    files in secrets_dir_path"""
    secrets: Mapping[str, Any] = {}
    if not secrets_dir_path:
        return secrets

    secrets_dir_path = Path(secrets_dir_path).expanduser()
    if not secrets_dir_path.exists():
        warnings.warn(f'directory "{secrets_dir_path}" does not exist')
        return secrets

    if not secrets_dir_path.is_dir():
        raise SettingsError(f'secrets_dir must reference a directory, not a {path_type(secrets_dir_path)}')

    return SecretSource(secrets_dir_path)


def dotenv_source_provider(
    env_file_paths: Optional[DotenvType], env_file_encoding: Optional[str] = None
) -> Mapping[str, Any]:
    """Returns dictionary with environment variables loaded from dotenv files"""
    try:
        from dotenv import dotenv_values
    except ImportError as e:
        raise ImportError('python-dotenv is not installed, run `pip install pydantic[dotenv]`') from e

    env_file_encoding = env_file_encoding if env_file_encoding else 'utf8'
    dotenv_vars: Dict[str, Any] = {}
    if env_file_paths is None:
        return dotenv_vars

    if isinstance(env_file_paths, (str, os.PathLike)):
        env_file_paths = [env_file_paths]

    for file_path in env_file_paths:
        file_path = Path(file_path).expanduser()
        if not file_path.is_file():
            continue
        dotenv_vars.update(dotenv_values(file_path, encoding=env_file_encoding))
    return dotenv_vars


def env_source_provider(env_file_paths: DotenvType, env_file_encoding: str = 'utf8') -> Mapping[str, Any]:
    """Returns diectionary with environment variables loaded from dotenv files and system environment"""
    env_vars: Dict[str, Any] = {}
    if env_file_paths:
        env_vars.update(dotenv_source_provider(env_file_paths, env_file_encoding))
    return {**env_vars, **os.environ}