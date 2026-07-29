"""Framework-level HTTP dependencies.

Authentication is deliberately absent here — it lands with the auth module,
which will own the scopes and the guard every router opts into. Until then
routers are open.
"""

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
    """
    Desc: Build a path dependency that decodes a public id to the internal one.
    Args:
        encryption (IDEncryption): The owning module's id encryption.
        entity (str): Name of the entity, for the not-found error.
        param (str): Name of the path parameter to read and decode.
    Returns:
        return (Callable[..., int]): A dependency mapping the public path
            id to the internal id.
    """

    def resolve(**path: int) -> int:
        """
        Desc: Decode a route's public id, 404-ing on a malformed one.
        Args:
            **path (int): The captured path parameters.
        Returns:
            return (int): The internal id.
        """
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
