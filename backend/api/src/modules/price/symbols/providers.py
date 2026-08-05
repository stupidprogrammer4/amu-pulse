from dishka import Provider, Scope, provide

from src.modules.price.symbols.app.services import SymbolService
from src.modules.price.symbols.infra.repository import SymbolRepository
from src.modules.price.symbols.interfaces import ISymbolService


class SymbolProvider(Provider):
    scope = Scope.REQUEST

    symbol_repo = provide(SymbolRepository)
    symbol_service = provide(SymbolService, provides=ISymbolService)
