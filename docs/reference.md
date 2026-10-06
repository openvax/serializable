# API reference

## Choose a base class

Use the dataclass mixin to preserve dataclass-generated methods. The original
base class supplies its own constructor-field introspection and object methods.

::: serializable.DataclassSerializable

::: serializable.Serializable

## Serialize supported values

The helpers also work with containers. The serializable representation records
Python types; the plain field dictionary and JSON string have different roles.

::: serializable.to_dict

::: serializable.to_json

::: serializable.from_json

::: serializable.to_serializable_repr

::: serializable.from_serializable_repr
