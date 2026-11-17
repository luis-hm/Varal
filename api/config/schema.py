from copy import deepcopy

from allauth.headless.spec.internal.schema import get_schema as get_headless_schema
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.openapi import AutoSchema
from openapi_spec_validator import validate


class VaralAutoSchema(AutoSchema):
    def _get_request_body(self, direction="request"):
        # DRF Spectacular omits DELETE bodies by default; RN30 deliberately requires
        # a CSRF-protected, typed confirmation in this one operation.
        if self.method == "DELETE" and self.path == "/api/me/" and direction == "request":
            from apps.privacidade.views import ConfirmacaoExclusaoSerializer

            component = self.resolve_serializer(ConfirmacaoExclusaoSerializer, direction)
            return {"required": True, "content": {"application/json": {"schema": component.ref}}}
        return super()._get_request_body(direction)


def namespace_components(value):
    """Keep native allauth contracts, without colliding with DRF components."""
    if isinstance(value, list):
        return [namespace_components(item) for item in value]
    if not isinstance(value, dict):
        return value
    result = {}
    for key, item in value.items():
        if key == "$ref" and item.startswith("#/components/"):
            parts = item.split("/")
            parts[3] = "Allauth" + parts[3]
            result[key] = "/".join(parts)
        elif key == "security":
            result[key] = [
                {"Allauth" + scheme: scopes for scheme, scopes in requirement.items()}
                for requirement in item
            ]
        else:
            result[key] = namespace_components(item)
    return result


def combine_schemas(drf, headless):
    schema = deepcopy(drf)
    native = namespace_components(headless)
    if schema["openapi"] != native["openapi"]:
        raise ValueError("Incompatible DRF and allauth OpenAPI versions")
    for path, operation in native["paths"].items():
        if path in schema["paths"]:
            raise ValueError(f"Duplicate OpenAPI path: {path}")
        schema["paths"][path] = operation
    for kind, components in native["components"].items():
        target = schema.setdefault("components", {}).setdefault(kind, {})
        for name, component in components.items():
            name = "Allauth" + name
            if name in target:
                raise ValueError(f"Duplicate OpenAPI component: {name}")
            target[name] = component
    schema["tags"] = schema.get("tags", []) + native.get("tags", [])
    validate(schema)
    return schema


class CombinedSchemaGenerator(SchemaGenerator):
    def get_schema(self, request=None, public=False):
        return combine_schemas(super().get_schema(request, public), get_headless_schema())
