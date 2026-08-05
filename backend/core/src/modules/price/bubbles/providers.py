from dishka import Provider, Scope, provide

from src.modules.price.bubbles.app.services import (
    BubbleConfigService,
    BubbleService,
)
from src.modules.price.bubbles.infra.repository import (
    BubbleConfigRepository,
    BubbleRepository,
)
from src.modules.price.bubbles.interfaces import (
    IBubbleConfigService,
    IBubbleService,
)


class BubbleProvider(Provider):
    scope = Scope.REQUEST

    bubble_repo = provide(BubbleRepository)
    bubble_config_repo = provide(BubbleConfigRepository)
    bubble_config_service = provide(
        BubbleConfigService, provides=IBubbleConfigService
    )
    bubble_service = provide(BubbleService, provides=IBubbleService)
