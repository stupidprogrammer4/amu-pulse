import importlib
import inspect
import pkgutil
from functools import cached_property, lru_cache

from dishka import Provider
from elasticsearch import AsyncElasticsearch
from elasticsearch.dsl import AsyncDocument
from fastapi import APIRouter

from src.core.logger import logger


class Bootstrapper:
    def __init__(self, base_pkg: str = "src.modules") -> None:
        self.base_pkg = base_pkg
        self.providers_path = "providers"
        self.models_path = "domain.models"
        self.routers_path = "routers"
        self.doc_path = "domain.documents"
        self.tasks_path = "tasks"

    @cached_property
    def submodules(self) -> list:
        modules = []
        base = importlib.import_module(self.base_pkg)
        for _, name, is_pkg in pkgutil.iter_modules(
            base.__path__, prefix=self.base_pkg + "."
        ):
            if is_pkg:
                if self._is_module(name):
                    modules.append(name)
                else:
                    group = importlib.import_module(name)
                    for _, sub_name, sub_is_pkg in pkgutil.iter_modules(
                        group.__path__, prefix=name + "."
                    ):
                        if sub_is_pkg and self._is_module(sub_name):
                            modules.append(sub_name)
        return modules

    def _is_module(self, name: str) -> bool:
        pkg = importlib.import_module(name)
        layers = {
            sub
            for _, sub, is_pkg in pkgutil.iter_modules(pkg.__path__)
            if is_pkg
        }
        return bool(layers & {"domain", "app"})

    def import_module(self, path: str, *, raise_nested: bool = False):
        module = None
        try:
            module = importlib.import_module(path)
        except ModuleNotFoundError as e:
            if raise_nested and e.name != path:
                raise
        return module

    def import_package_modules(
        self, path: str, *, raise_nested: bool = False
    ) -> list:
        modules = []
        package = self.import_module(path, raise_nested=raise_nested)
        if package is not None and hasattr(package, "__path__"):
            for _, name, is_pkg in pkgutil.iter_modules(
                package.__path__, prefix=path + "."
            ):
                if not is_pkg:
                    module = self.import_module(
                        name, raise_nested=raise_nested
                    )
                    if module is not None:
                        modules.append(module)
        return modules

    def boot_routers(self) -> list[APIRouter]:
        routers = []
        for module_name in self.submodules:
            files = self.import_package_modules(
                f"{module_name}.{self.routers_path}", raise_nested=True
            )
            for module in files:
                for _, obj in inspect.getmembers(module):
                    if isinstance(obj, APIRouter) and not any(
                        obj is seen for seen in routers
                    ):
                        routers.append(obj)
        return routers

    def boot_sqlmodels(self) -> None:
        for module_name in self.submodules:
            self.import_module(f"{module_name}.{self.models_path}")

    def boot_providers(self) -> list[Provider]:
        providers = []
        for module_name in self.submodules:
            module = self.import_module(f"{module_name}.{self.providers_path}")
            if module:
                for _, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, Provider)
                        and obj is not Provider
                        and obj.__module__.startswith(self.base_pkg)
                    ):
                        providers.append(obj())
        return providers

    def boot_documents(self) -> list[type[AsyncDocument]]:
        es_documents = []
        for module_name in self.submodules:
            module = self.import_module(f"{module_name}.{self.doc_path}")
            if module:
                for _, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, AsyncDocument)
                        and obj is not AsyncDocument
                    ):
                        es_documents.append(obj)
        return es_documents

    def boot_tasks(self) -> None:
        for module_name in self.submodules:
            self.import_package_modules(f"{module_name}.{self.tasks_path}")

    async def boot_es_indices(self, es: AsyncElasticsearch) -> None:
        for document in self.boot_documents():
            index_name = document._index._name
            try:
                if not await es.indices.exists(index=index_name):
                    await document.init(using=es)
            except Exception as exc:  # noqa: BLE001 — boot must survive a down ES
                logger.warning(
                    f"skipping ES index init for {index_name}: {exc}"
                )


@lru_cache
def get_bootstrapper():
    return Bootstrapper()
