from inspect import Parameter, Signature
from typing import Callable

from src.common.bases.encryption import IDEncryption
from src.common.errors.exceptions import NotFoundException
from src.core import resources


def decode_path_id(
    encryption: IDEncryption,
    entity: str,
    param: str = "id",
) -> Callable[..., int]:

    def resolve(**path: int) -> int:
        public_id = path[param]
        internal = encryption.try_decode(public_id)
        if internal is None:
            raise NotFoundException(
                message=f"No {entity} with id '{public_id}'",
                message_code=resources.NOT_FOUND_ERROR,
                entity=entity,
                identifier="id",
                identifier_value=public_id,
            )
        return internal

    resolve.__signature__ = Signature(
        [Parameter(param, Parameter.POSITIONAL_OR_KEYWORD, annotation=int)]
    )
    return resolve
