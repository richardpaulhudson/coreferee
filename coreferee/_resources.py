# -*- coding: utf-8 -*-
"""Resource path/listing compatibility: importlib.resources.files() on 3.9+, pkg_resources on 3.6-3.8."""

import sys

if sys.version_info >= (3, 9):
    from importlib.resources import files as _resource_files

    def resource_path(package: str, *path_parts: str) -> str:
        if not path_parts:
            return str(_resource_files(package))
        return str(_resource_files(package).joinpath(*path_parts))

    def resource_exists(package: str, *path_parts: str) -> bool:
        if not path_parts:
            return True
        return _resource_files(package).joinpath(*path_parts).is_file()

    def resource_listdir(package: str, *path_parts: str):
        base = _resource_files(package)
        if path_parts:
            base = base.joinpath(*path_parts)
        return [p.name for p in base.iterdir()]

else:
    import pkg_resources

    def _path_str(*path_parts: str) -> str:
        return "/".join(path_parts) if path_parts else ""

    def resource_path(package: str, *path_parts: str) -> str:
        return pkg_resources.resource_filename(package, _path_str(*path_parts))

    def resource_exists(package: str, *path_parts: str) -> bool:
        return pkg_resources.resource_exists(package, _path_str(*path_parts))

    def resource_listdir(package: str, *path_parts: str):
        return pkg_resources.resource_listdir(package, _path_str(*path_parts))
