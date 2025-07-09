from __future__ import annotations

import re
from functools import cached_property
from types import GenericAlias, UnionType
from typing import (
    Any,
    Generic,
    Iterable,
    Literal,
    Self,
    Sequence,
    TypeVar,
    cast,
    get_args,
    get_origin,
)

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator, model_validator


def _validate_unique_names(
    value: list[str] | dict[str, list[str]],
) -> list[str] | dict[str, list[str]]:
    if isinstance(value, list):
        if len(value) != len(set(value)):
            raise ValueError("Duplicate names in list")
        return value
    else:
        return {k: cast(list[str], _validate_unique_names(v)) for k, v in value.items()}


def handle_list_yml_format(value: Iterable[Any]) -> Any:
    """Normalize legacy YAML list-of-dict patterns.

    Only lists whose *elements* are dictionaries are converted.  Plain lists (e.g. a
    list of strings) are returned unchanged so that typed fields such as
    ``labels: list[str]`` continue to validate correctly.
    """

    if not (isinstance(value, list) and value and all(isinstance(i, dict) for i in value)):
        return value

    value_dicts: list[dict[str, Any]] = cast(list[dict[str, Any]], value)

    # Case A: list of single-key mappings → merge into one mapping.
    if all(len(item) == 1 for item in value_dicts):
        merged: dict[str, Any] = {}
        for item in value_dicts:
            merged.update(item)
        return merged

    # Case B: list with exactly one mapping → unwrap it.
    if len(value_dicts) == 1:
        return value_dicts[0]

    # Otherwise leave as-is (multi-entry list of mappings).
    return value


class YMLModel(BaseModel):
    """Base model for models defined in YAML files."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__class__.model_fields.keys()}


TYML = TypeVar("TYML", bound=YMLModel)


class SpecModel(BaseModel, Generic[TYML]):
    """Base model for models used in auth flows."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    @field_validator("*", mode="before")
    @classmethod
    def convert_from_yml(cls, value: Any, info: ValidationInfo) -> Any:
        if not value:
            return value

        field_name = info.field_name
        if not field_name:
            return value

        annotation = cls.model_fields[field_name].annotation

        # If the model is being instantiated programmatically (not via .from_yml),
        # we may not have YAML context available.  In that case skip the YAML
        # reference-resolution logic and return the value unchanged.
        if not info.context:
            return value

        fields_map = info.context["fields_map"]
        pages_map = info.context["pages_map"]

        if isinstance(annotation, type) and issubclass(annotation, SpecModel):  # for FlowModel
            return annotation.from_yml(value, fields_map=fields_map, pages_map=pages_map)  # type: ignore
        elif isinstance(annotation, GenericAlias):  # for list[FlowModel] or dict[str, FlowModel]
            origin = get_origin(annotation)
            if origin is list:
                base = get_args(annotation)[0]
                if issubclass(base, SpecModel) and isinstance(value[0], YMLModel):
                    return [
                        base.from_yml(v, fields_map=fields_map, pages_map=pages_map)  # type: ignore
                        for v in value
                    ]
            elif origin is dict:
                base = get_args(annotation)[1]
                if issubclass(base, SpecModel) and isinstance(next(iter(value)), YMLModel):
                    return {
                        k: base.from_yml(v, fields_map=fields_map, pages_map=pages_map)  # type: ignore
                        for k, v in value.items()
                    }
            else:
                raise ValueError(f"Unsupported generic type: {annotation}")
        elif isinstance(annotation, UnionType):  # for FlowModel | None # type: ignore
            base = get_args(annotation)[0]
            if issubclass(base, SpecModel) and isinstance(value, YMLModel):
                return base.from_yml(value, fields_map=fields_map, pages_map=pages_map)  # type: ignore

        return handle_list_yml_format(value)

    @classmethod
    def _data_from_yml(
        cls, yml: TYML, *, fields_map: dict[str, FieldYML], pages_map: dict[str, PageSpecYML]
    ) -> dict[str, Any]:
        data = yml.to_dict()

        if data.get("fields"):
            data["fields"] = cls._str_to_spec(data["fields"], fields_map)
        if data.get("pages"):
            data["pages"] = cls._str_to_spec(data["pages"], pages_map)
        return data

    @classmethod
    def _str_to_spec(cls, value: Any, map: dict[str, Any]) -> Any:
        if isinstance(value, YMLModel):
            return value
        elif isinstance(value, str):
            if value not in map:
                raise ValueError(f"Unknown field or page name: {value}")
            return map[value]
        elif isinstance(value, list):
            return [cls._str_to_spec(v, map) for v in cast(list[Any], value)]
        elif isinstance(value, dict):
            return {k: cls._str_to_spec(v, map) for k, v in cast(dict[str, Any], value).items()}
        else:
            raise ValueError(f"Unsupported field type: {type(value)}")

    @classmethod
    def from_yml(
        cls, yml: TYML, *, fields_map: dict[str, FieldYML], pages_map: dict[str, PageSpecYML]
    ) -> Self:
        return cls.model_validate(
            cls._data_from_yml(yml, fields_map=fields_map, pages_map=pages_map),
            context={"fields_map": fields_map, "pages_map": pages_map},
        )


class FieldYML(YMLModel):
    name: str
    type: Literal[
        "text",
        "email",
        "password",
        "autoclick",
        "click",
        "press",
        "navigate",
        "wait",
        "message",
        "selection",
    ]
    prompt: str | None = None
    label: str | None = None
    iframe_selector: str | None = None
    selector: str | None = None
    selectors: str | None = None
    url: str | None = None
    expect_nav: bool = False
    delay_ms: int | None = None

    @model_validator(mode="after")
    def validate_selectors(self) -> Self:
        if self.type == "navigate":
            assert self.url is not None, "URL is required for navigate field"
            assert self.expect_nav is not False, "expect_nav must be True for navigate field"
            return self
        elif self.type != "selection":
            # For normal interactive fields exactly one of selector/selectors is required.
            # Dynamic "selection" fields derive their target via ``option_items`` at runtime,
            # so they are exempt.
            assert bool(self.selector) ^ bool(self.selectors), (
                "One and only one of selector and selectors must be provided for non-navigate fields"
            )
        return self

    @model_validator(mode="after")
    def validate_prompt(self) -> Self:
        if self.type not in ["wait", "navigate", "autoclick", "selection"]:
            assert self.prompt is not None, "prompt is required for fields that need input"
        return self


class Field(SpecModel[FieldYML]):
    name: str
    type: Literal[
        "text",
        "email",
        "password",
        "autoclick",
        "click",
        "press",
        "navigate",
        "wait",
        "message",
        "selection",
    ]
    prompt: str | None = None
    label: str | None = None
    iframe_selector: str | None = None
    selector: str | None = None
    selectors: str | None = None
    # Dynamic selection helpers (only used when type == 'selection')
    option_items: str | None = None
    option_label: str | None = None
    url: str | None = None
    expect_nav: bool
    delay_ms: int | None = None

    @property
    def needs_input(self) -> bool:
        return self.type in ["text", "email", "password", "click", "press", "selection"]

    @property
    def needs_action(self) -> bool:
        return self.type in [
            "autoclick",
            "click",
            "press",
            "text",
            "email",
            "password",
            "navigate",
            "selection",
        ]


class GraphQLListenerYML(YMLModel):
    endpoint: str
    operation: str
    function: str | None = None


class GraphQLListener(SpecModel[GraphQLListenerYML]):
    endpoint: str
    operation: str
    function: str | None = None


class StepYML(YMLModel):
    name: str
    timeout: int | None = None
    sleep: int | None = None
    url: str | None = None
    wait_for_selector: str | None = None
    wait_for_url: str | re.Pattern[str] | None = None
    fields: Sequence[FieldYML | str] = []
    click: str | None = None
    press: str | None = None
    bundle: str | None = None
    slurp_selector: str | None = None
    listen_to_url_stub_json: str | None = None
    graphql: GraphQLListenerYML | None = None
    pause: str | None = None
    download_filename: str | None = None


class Step(SpecModel[StepYML]):
    name: str
    timeout: int | None = None
    sleep: int | None = None
    url: str | None = None
    wait_for_selector: str | None = None
    wait_for_url: str | re.Pattern[str] | None = None
    fields: list[Field] = []
    click: str | None = None
    press: str | None = None
    bundle: str | None = None
    slurp_selector: str | None = None
    listen_to_url_stub_json: str | None = None
    graphql: GraphQLListenerYML | None = None
    pause: str | None = None
    download_filename: str | None = None


class ChoiceYML(YMLModel):
    name: str
    prompt: str | None = None
    fields: list[str] | dict[Literal["required", "optional"], list[str]]


class Choice(SpecModel[ChoiceYML]):
    name: str
    prompt: str | None = None
    required_fields: list[Field]
    optional_fields: list[Field] = []

    @classmethod
    def from_yml(
        cls, yml: ChoiceYML, *, fields_map: dict[str, FieldYML], pages_map: dict[str, PageSpecYML]
    ) -> Self:
        data = super()._data_from_yml(yml, fields_map=fields_map, pages_map=pages_map)
        fields: dict[Literal["required", "optional"], list[Field]] = data.pop("fields", dict())
        if isinstance(fields, list):
            data["required_fields"] = fields
        else:
            data["required_fields"] = fields.get("required", [])
            data["optional_fields"] = fields.get("optional", [])
        return cls.model_validate(data, context={"fields_map": fields_map, "pages_map": pages_map})

    def is_filled(self, inputs: dict[str, Any]) -> bool:
        return all(
            inputs.get(field.name) is not None
            for field in self.required_fields
            if field.needs_input
        )

    @property
    def fields_accept_input(self) -> list[Field]:
        return [f for f in self.required_fields + self.optional_fields if f.needs_input]

    @property
    def fields_need_action(self) -> list[Field]:
        return [f for f in self.required_fields + self.optional_fields if f.needs_action]

    @property
    def all_fields(self) -> list[Field]:
        return self.required_fields + self.optional_fields


class DynamicChoicesYML(YMLModel):
    option_items: str
    option_label: str | None = None


class DynamicChoices(DynamicChoicesYML):
    """Runtime counterpart - identical for now."""


class ChoicesYML(YMLModel):
    name: str
    prompt: str
    groups: list[ChoiceYML] = []
    dynamic: DynamicChoicesYML | None = None
    afterwards: list[str] = []


class Choices(SpecModel[ChoicesYML]):
    name: str
    prompt: str
    groups: list[Choice]
    dynamic: DynamicChoices | None = None
    afterwards: list[Field] = []

    @classmethod
    def from_yml(
        cls,
        yml: ChoicesYML,
        *,
        fields_map: dict[str, FieldYML],
        pages_map: dict[str, PageSpecYML],
    ) -> Self:
        # Convert static groups via parent helper first (may be empty).
        data = cls._data_from_yml(yml, fields_map=fields_map, pages_map=pages_map)

        # Resolve "afterwards" into concrete Field objects.
        afterwards_fields: list[Field] = []
        for fname in yml.afterwards:
            if fname not in fields_map:
                raise ValueError(f"Unknown field name in choices.afterwards: {fname}")
            afterwards_fields.append(
                Field.from_yml(
                    fields_map[fname],
                    fields_map=fields_map,
                    pages_map=pages_map,
                )
            )

        if afterwards_fields:
            data["afterwards"] = afterwards_fields

        if yml.dynamic is not None:
            # Convert the pydantic model to a plain dict so DynamicChoices can
            # re-validate it with the appropriate target model.  At this point
            # ``yml.dynamic`` is guaranteed to be a ``DynamicChoicesYML``
            # instance (validated by Pydantic), so the cast is safe.
            dyn_src: dict[str, Any] = yml.dynamic.to_dict()  # type: ignore[arg-type]
            data["dynamic"] = DynamicChoices.model_validate(dyn_src)

        return cls.model_validate(data, context={"fields_map": fields_map, "pages_map": pages_map})


class PageSpecYML(YMLModel):
    name: str
    url: str | None = None
    timeout: int | None = None
    fields: list[str] | dict[Literal["required", "optional"], list[str]] = []
    choices: ChoicesYML | None = None
    message: str | None = None
    end: bool = False

    # ------------------------------------------------------------------
    # Legacy YAML compatibility: allow writing `choices:` as a list of
    # single-key mappings (dash style).  Merge into a single dictionary
    # before normal validation.
    # ------------------------------------------------------------------
    @field_validator("choices", mode="before")
    @classmethod
    def _merge_choices_singleton_list(cls, value: Any) -> Any:
        return handle_list_yml_format(value)

    @model_validator(mode="after")
    def validate_fields_and_choices(self) -> Self:
        if self.fields and self.choices:
            raise ValueError("Cannot specify both fields and choices")

        if self.fields:
            if isinstance(self.fields, list):
                _validate_unique_names(self.fields)
            else:
                _validate_unique_names([f for lst in self.fields.values() for f in lst])
        return self


class PageSpec(SpecModel[PageSpecYML]):
    name: str
    url: str | None = None
    timeout: int | None = None
    end: bool = False
    message: str | None = None
    choices: Choices | None = None

    @classmethod
    def from_yml(
        cls, yml: PageSpecYML, *, fields_map: dict[str, FieldYML], pages_map: dict[str, PageSpecYML]
    ) -> Self:
        choices: Choices | None = None

        if yml.fields:
            # Build an implicit single-choice wrapper around the raw fields list/dict.
            stub_choices_yml = ChoicesYML.model_validate({
                "name": "",
                "prompt": "",
                "groups": [{"name": "", "prompt": "", "fields": yml.fields}],
            })
            choices = Choices.from_yml(
                stub_choices_yml,
                fields_map=fields_map,
                pages_map=pages_map,
            )
        elif yml.choices is not None:
            # Use the explicit choices block.
            choices = Choices.from_yml(
                yml.choices,
                fields_map=fields_map,
                pages_map=pages_map,
            )

        data = super()._data_from_yml(yml, fields_map=fields_map, pages_map=pages_map)
        # Remove the raw 'fields' entry; we store it inside choices instead.
        data.pop("fields", None)

        if choices is not None:
            data["choices"] = choices

        return cls.model_validate(data, context={"fields_map": fields_map, "pages_map": pages_map})

    def fields(
        self, *, include: Literal["required", "optional", "all"] = "required"
    ) -> list[Field]:
        if not self.choices:
            return []

        results: list[Field] = []
        if include in ["required", "all"]:
            results.extend([f for group in self.choices.groups for f in group.required_fields])
            # Unconditional follow-up actions belong to the page regardless of which choice is picked.
            # Treat them as *required* so the detector expects them to be present.
            results.extend(self.choices.afterwards)
        if include in ["optional", "all"]:
            results.extend([f for group in self.choices.groups for f in group.optional_fields])
        return results


class FlowYML(YMLModel):
    fields: list[FieldYML] = []
    pages: list[PageSpecYML] = []
    steps: list[StepYML] = []
    start: str | None = None

    @cached_property
    def fields_map(self) -> dict[str, FieldYML]:
        return {f.name: f for f in self.fields}

    @cached_property
    def pages_map(self) -> dict[str, PageSpecYML]:
        return {p.name: p for p in self.pages}

    @model_validator(mode="after")
    def _validate_unique_page_and_field_names(self) -> FlowYML:
        # Ensure that page and field names are unique.
        _validate_unique_names([p.name for p in self.pages])
        _validate_unique_names([f.name for f in self.fields])

        return self


class Flow(SpecModel[FlowYML]):
    fields: list[Field] = []
    pages: list[PageSpec] = []
    steps: list[Step] = []
    start: PageSpec | str | None = None

    @classmethod
    def from_yml(
        cls, yml: FlowYML, *, pages_map: dict[str, PageSpecYML], fields_map: dict[str, FieldYML]
    ) -> Self:
        data = super()._data_from_yml(yml, fields_map=fields_map, pages_map=pages_map)
        if data.get("pages"):
            assert data.get("start"), "start is required if pages are defined"

        if data.get("start"):
            if data["start"] in pages_map:
                data["start"] = pages_map[data["start"]]

        flow = cls.model_validate(data, context={"fields_map": fields_map, "pages_map": pages_map})

        # Add universal pages to FSM-style flows
        if flow.pages:
            from getgather.detect import get_universal_pages

            universal_pages = get_universal_pages()

            # Create new flow with universal pages added
            flow_data = flow.model_dump()
            flow_data["pages"] = flow.pages + universal_pages
            flow = cls.model_validate(flow_data)

        return flow

    @cached_property
    def fields_map(self) -> dict[str, Field]:
        return {f.name: f for f in self.fields}


class ColumnYML(YMLModel):
    name: str
    selector: str
    attribute: str | None = None
    multiple: bool = False


class Column(SpecModel[ColumnYML]):
    name: str
    selector: str
    attribute: str | None = None
    multiple: bool = False


class SchemaYML(YMLModel):
    bundle: str
    format: Literal["html"]
    output: str
    row_selector: str
    columns: list[ColumnYML]


class Schema(SpecModel[SchemaYML]):
    bundle: str
    format: Literal["html"]
    output: str
    row_selector: str
    columns: list[Column]


class BrandSpecYML(YMLModel):
    id: str
    name: str
    auth: FlowYML
    extract: FlowYML | None = None
    parse: list[SchemaYML] = []


class BrandSpec(SpecModel[BrandSpecYML]):
    id: str
    name: str
    auth: Flow
    extract: Flow | None = None
    parse: list[Schema] = []
