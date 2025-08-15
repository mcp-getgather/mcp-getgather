import pytest
import yaml
from assertpy import assert_that

from getgather.connectors.spec_models import (
    Field,
    FieldYML,
    Flow,
    FlowYML,
    PageSpec,
    PageSpecYML,
)
from getgather.yaml_utils import RegexLoader


def test_field():
    txt = """
    fields:
      - name: field_with_selector
        type: email
        prompt: Enter your email
        selector: input[name="email"]
      - name: navigate_field
        type: navigate
        prompt: Navigate to the page
        url: https://example.com
        expect_nav: true
    """
    yml = yaml.load(txt, Loader=RegexLoader)
    spec = [
        Field.from_yml(FieldYML.model_validate(f), fields_map={}, pages_map={})
        for f in yml["fields"]
    ]
    assert len(spec) == 2


def test_field_without_selector():
    txt = """
    fields:
      - name: field_without_selector
        type: text
        prompt: Enter your text
    """
    yml = yaml.load(txt, Loader=RegexLoader)
    with pytest.raises(ValueError, match="selector is required for non-selection fields"):
        [
            Field.from_yml(FieldYML.model_validate(f), fields_map={}, pages_map={})
            for f in yml["fields"]
        ]


def test_navigate_field_without_url():
    txt = """
    fields:
      - name: navigate_field
        type: navigate
        prompt: Navigate to the page
        expect_nav: true
    """
    yml = yaml.load(txt, Loader=RegexLoader)
    with pytest.raises(ValueError, match="URL is required"):
        [
            Field.from_yml(FieldYML.model_validate(f), fields_map={}, pages_map={})
            for f in yml["fields"]
        ]


def test_navigate_field_without_expect_nav():
    txt = """
    fields:
      - name: navigate_field
        type: navigate
        prompt: Navigate to the page
        url: https://example.com
    """
    yml = yaml.load(txt, Loader=RegexLoader)
    with pytest.raises(ValueError, match="expect_nav must be True"):
        [
            Field.from_yml(FieldYML.model_validate(f), fields_map={}, pages_map={})
            for f in yml["fields"]
        ]


def test_page_with_required_fields():
    txt = """
    fields:
      - name: field
        type: text
        prompt: Enter your text
        selector: input[name="text"]
    pages:
      - name: page_with_fields
        url: https://example.com
        fields: [field]
    """
    yml = yaml.load(txt, Loader=RegexLoader)
    field_yml_models = [FieldYML.model_validate(f) for f in yml["fields"]]
    fields_map = {f.name: f for f in field_yml_models}
    spec = [
        PageSpec.from_yml(PageSpecYML.model_validate(p), fields_map=fields_map, pages_map={})
        for p in yml["pages"]
    ]
    field_spec_model = Field.from_yml(field_yml_models[0], fields_map={}, pages_map={})

    assert spec[0].choices is not None
    assert spec[0].choices.groups[0].required_fields == [field_spec_model]
    assert spec[0].choices.groups[0].optional_fields == []
    assert spec[0].fields() == [field_spec_model]


def test_page_with_optional_fields():
    txt = """
    fields:
      - name: required_field
        type: text
        prompt: Enter your text
        selector: input[name="text"]
      - name: optional_field
        type: text
        prompt: Enter your text
        selector: input[name="text"]
    pages:
      - name: page_with_fields
        url: https://example.com
        fields:
          required: [required_field]
          optional: [optional_field]
    """
    yml = yaml.load(txt, Loader=RegexLoader)
    field_yml_models = [FieldYML.model_validate(f) for f in yml["fields"]]
    fields_map = {f.name: f for f in field_yml_models}
    spec = [
        PageSpec.from_yml(PageSpecYML.model_validate(p), fields_map=fields_map, pages_map={})
        for p in yml["pages"]
    ]
    required_field_spec_model = Field.from_yml(
        fields_map["required_field"], fields_map={}, pages_map={}
    )
    optional_field_spec_model = Field.from_yml(
        fields_map["optional_field"], fields_map={}, pages_map={}
    )

    assert spec[0].choices is not None
    assert len(spec[0].choices.groups) == 1
    assert spec[0].choices.groups[0].required_fields == [required_field_spec_model]
    assert spec[0].choices.groups[0].optional_fields == [optional_field_spec_model]
    assert_that(spec[0].fields(include="all")).is_length(2)
    assert_that(spec[0].fields(include="all")).contains(
        required_field_spec_model, optional_field_spec_model
    )


def test_page_with_invalid_fields():
    txt = """
    fields:
      - name: field
        type: text
        prompt: Enter your text
    pages:
      - name: page
        url: https://example.com
        fields: [invalid_field]
    """
    yml = yaml.load(txt, Loader=RegexLoader)
    with pytest.raises(ValueError, match="Unknown field"):
        [
            PageSpec.from_yml(PageSpecYML.model_validate(p), fields_map={}, pages_map={})
            for p in yml["pages"]
        ]


def test_page_with_choices():
    txt = """
    fields:
      - name: field_1
        type: text
        prompt: Enter your text
        selector: input[name="text"]
      - name: field_2
        type: text
        prompt: Enter your text
        selector: input[name="text"]
    pages:
      - name: page_with_choices
        url: https://example.com
        choices:
          name: a list of choices
          prompt: Choose one of the following options
          groups:
            - name: choice_1
              prompt: Enter your text
              fields: [field_1]
            - name: choice_2
              prompt: Enter your text
              fields: [field_2]
    """
    yml = yaml.load(txt, Loader=RegexLoader)
    field_yml_models = [FieldYML.model_validate(f) for f in yml["fields"]]
    fields_map = {f.name: f for f in field_yml_models}
    spec = [
        PageSpec.from_yml(PageSpecYML.model_validate(p), fields_map=fields_map, pages_map={})
        for p in yml["pages"]
    ]
    field_1_spec_model = Field.from_yml(fields_map["field_1"], fields_map={}, pages_map={})
    field_2_spec_model = Field.from_yml(fields_map["field_2"], fields_map={}, pages_map={})
    assert spec[0].choices is not None
    assert len(spec[0].choices.groups) == 2
    assert spec[0].choices.groups[0].required_fields == [field_1_spec_model]
    assert spec[0].choices.groups[1].required_fields == [field_2_spec_model]
    assert_that(spec[0].fields(include="all")).is_length(2)
    assert_that(spec[0].fields(include="all")).contains(field_1_spec_model, field_2_spec_model)


def test_flow():
    txt = """
    auth:
      fields:
        - name: field
          type: text
          prompt: Enter your text
          selector: input[name="text"]
      pages:
        - name: page_with_fields
          url: https://example.com
          fields: [field]
      start: page_with_fields
    """
    yml = yaml.load(txt, Loader=RegexLoader)
    field_yml_models = [FieldYML.model_validate(f) for f in yml["auth"]["fields"]]
    fields_map = {f.name: f for f in field_yml_models}
    pages_yml_models = [PageSpecYML.model_validate(p) for p in yml["auth"]["pages"]]
    pages_map = {p.name: p for p in pages_yml_models}
    spec = Flow.from_yml(
        FlowYML.model_validate(yml["auth"]), fields_map=fields_map, pages_map=pages_map
    )
    expected_field = Field.from_yml(field_yml_models[0], fields_map={}, pages_map={})
    expected_page = PageSpec.from_yml(
        pages_yml_models[0], fields_map=fields_map, pages_map=pages_map
    )

    # Test fields (unchanged)
    assert spec.fields == [expected_field]

    # Test that brand-specific page is included (allows for additional universal pages)
    brand_page_names = [p.name for p in spec.pages]
    assert "page_with_fields" in brand_page_names, (
        f"Expected page_with_fields in {brand_page_names}"
    )

    # Test that the actual page content is correct for the brand page
    brand_page = next(p for p in spec.pages if p.name == "page_with_fields")
    assert brand_page.name == expected_page.name, (
        f"Expected {expected_page.name} but got {brand_page.name}"
    )
    assert brand_page.url == expected_page.url, (
        f"Expected {expected_page.url} but got {brand_page.url}"
    )

    assert len(spec.pages) == 3, (
        f"Expected 3 pages but got {len(spec.pages)}"
    )  # includes the two universal pages and the brand-specific page


def test_flow_without_start():
    txt = """
    auth:
      fields:
        - name: field
          type: text
          prompt: Enter your text
          selector: input[name="text"]
      pages:
        - name: page
          url: https://example.com
          fields: [field]
    """
    yml = yaml.load(txt, Loader=RegexLoader)
    with pytest.raises(Exception, match="start is required"):
        Flow.from_yml(FlowYML.model_validate(yml["auth"]), fields_map={}, pages_map={})
