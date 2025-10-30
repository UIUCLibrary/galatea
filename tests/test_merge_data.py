import io
import os
import pathlib
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib
from unittest.mock import MagicMock, ANY, Mock
import xml.etree.ElementTree as ET
import pytest

from jinja2 import Template

from galatea import merge_data


def test_generate_mapping_file_for_tsv_calls_strategy() -> None:
    """Test that generate_mapping_file_for_tsv calls the writing strategy."""
    mock_writing_strategy = Mock()
    headers_reading_strategy = Mock(return_value=["header1", "header2"])

    mock_output_file = MagicMock()

    mock_tsv_file = Mock(spec_set=pathlib.Path)
    mock_tsv_file.name = "test.tsv"

    merge_data.generate_mapping_file_for_tsv(
        mock_tsv_file,
        mock_output_file,
        headers_reading_strategy=headers_reading_strategy,
        writing_strategy=mock_writing_strategy,
    )

    mock_writing_strategy.assert_called_once_with(
        "test.tsv", ["header1", "header2"], mock_output_file.open().__enter__()
    )


def test_get_keys_from_tsv():
    strategy = Mock()
    tsv_file = MagicMock()
    merge_data.get_keys_from_tsv(tsv_file, strategy)
    strategy.assert_called_once_with(tsv_file.open("r").__enter__())


def test_get_keys_from_tsv_fp():
    sample_tsv_file = io.StringIO("header1\theader2\nOne\ttwo")
    result = merge_data.get_keys_from_tsv_fp(sample_tsv_file)
    assert result == ["header1", "header2"]


@pytest.mark.parametrize(
    "key, expected_value",
    [
        ("key", "header1"),
        ("delimiter", "||"),
        ("matching_marc_fields", []),
        ("existing_data", "keep"),
    ],
)
def test_generate_mapping_toml_file_for_tsv_fp(key, expected_value):
    fp = io.StringIO()
    merge_data.generate_mapping_toml_file_for_tsv_fp(
        "spam.tsv", ["header1", "header2"], fp
    )
    assert tomllib.loads(fp.getvalue())["mapping"][0][key] == expected_value


SAMPLE_MAPPING_FILE_CONTENTS = b"""
[mappings]
identifier_key = "Bibliographic Identifier"  

[[mapping]]
key = "Uniform Title"
matching_marc_fields = []
delimiter = "||"
existing_data = "keep"
""".lstrip()

SAMPLE_ALMA_RECORD = """
<record xmlns="http://www.loc.gov/MARC21/slim" 
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
        xsi:schemaLocation="http://www.loc.gov/MARC21/slim 
                            http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd">
<datafield ind1=" " ind2=" " tag="120">
<subfield code="a">Bacon</subfield>
<subfield code="c">Eggs</subfield>
</datafield>
<datafield ind1=" " ind2=" " tag="040">
    <subfield code="a">PUL</subfield>
    <subfield code="b">eng</subfield>
    <subfield code="c">PUL</subfield>
    <subfield code="d">TJC</subfield>
    <subfield code="d">OCLCQ</subfield>
    <subfield code="d">OCLCG</subfield>
    <subfield code="d">OCLCF</subfield>
    <subfield code="d">OCLCO</subfield>
    <subfield code="d">OCLCA</subfield>
</datafield>
</record>
""".lstrip()


@pytest.mark.parametrize(
    "key, expected_value",
    [
        ("key", "Uniform Title"),
        ("matching_keys", []),
        ("delimiter", "||"),
        ("existing_data", "keep"),
    ],
)
def test_read_mapping_toml_data(key, expected_value):
    mapping_file_fp = io.BytesIO(SAMPLE_MAPPING_FILE_CONTENTS)

    assert (
        getattr(
            merge_data.read_mapping_toml_data(
                mapping_file_fp=mapping_file_fp,
                mapping_to_config_strategy=merge_data.map_marc_mapping_to_mapping_config,
            )["Uniform Title"],
            key,
        )
        == expected_value
    )


def test_read_mapping_toml_data_invalid():
    sample_mapping_file_fp = io.BytesIO(
        b"""
[mappings]
[[mapping]]
[key]
""".lstrip()
    )
    with pytest.raises(merge_data.BadMappingDataError):
        merge_data.read_mapping_toml_data(
            mapping_file_fp=sample_mapping_file_fp
        )


def test_get_identifier_key():
    mock_file = MagicMock()
    mock_strategy = Mock()
    merge_data.get_identifier_key(mock_file, mock_strategy)
    mock_strategy.assert_called_once_with(mock_file.open("rb").__enter__())


def test_get_identifier_key_fp():
    sample_mapping_file_fp = io.BytesIO(SAMPLE_MAPPING_FILE_CONTENTS)
    result = merge_data.get_identifier_key_fp(sample_mapping_file_fp)
    assert result == "Bibliographic Identifier"


def test_get_identifier_key_fp_invalid():
    sample_mapping_file_fp = io.BytesIO(b"""[mappings]""")
    with pytest.raises(merge_data.BadMappingDataError):
        merge_data.get_identifier_key_fp(sample_mapping_file_fp)


def test_merge_from_getmarc_uses_row_merge_data_strategy(monkeypatch):
    input_metadata_tsv_file = MagicMock()
    output_metadata_tsv_file = MagicMock()
    mapping_file = MagicMock()
    row_merge_data_strategy = Mock()
    monkeypatch.setattr(
        merge_data.tsv, "get_tsv_dialect", lambda _: "excel-tab"
    )
    merge_data.merge_from_getmarc(
        input_metadata_tsv_file,
        output_metadata_tsv_file,
        mapping_file,
        "spamserver",
        row_merge_data_strategy,
        Mock(name="write_to_file_strategy"),
    )
    row_merge_data_strategy.assert_called_once_with(
        mapping_file.open("rb").__enter__(),
        input_metadata_tsv_file.open("rb").__enter__(),
        ANY,
        "excel-tab",
        False,
    )


def test_merge_from_getmarc_uses_write_merge_data_strategy(monkeypatch):
    input_metadata_tsv_file = MagicMock()
    output_metadata_tsv_file = MagicMock()
    mapping_file = MagicMock()
    write_to_file_strategy = Mock()
    monkeypatch.setattr(
        merge_data.tsv, "get_tsv_dialect", lambda _: "excel-tab"
    )
    merge_data.merge_from_getmarc(
        input_metadata_tsv_file,
        output_metadata_tsv_file,
        mapping_file,
        "spamserver",
        Mock(name="row_merge_data_strategy", return_value=[{"some": "data"}]),
        write_to_file_strategy,
    )

    write_to_file_strategy.assert_called_once_with(
        [{"some": "data"}],
        "excel-tab",
        output_metadata_tsv_file.open("rb").__enter__(),
    )


SAMPLE_METADATA_TSV_FILE_CONTENTS = """
"Uniform Title"	"Bibliographic Identifier"
""	"dummy_id"
""".lstrip()


def test_merge_data_from_getmarc_uses_getmarc_strategy():
    get_marc_server_strategy = Mock(return_value="Bacon")
    merge_data.merge_data_from_getmarc(
        io.BytesIO(SAMPLE_MAPPING_FILE_CONTENTS),
        input_metadata_tsv_fp=io.StringIO(SAMPLE_METADATA_TSV_FILE_CONTENTS),
        get_marc_server_strategy=get_marc_server_strategy,
        dialect="excel-tab",
    )
    get_marc_server_strategy.assert_called_once_with("dummy_id")


def test_merge_data_from_getmarc_captures_line_in_serialization_error(monkeypatch):
    get_marc_server_strategy = Mock(return_value="Bacon")
    monkeypatch.setattr(merge_data.MergeRowData, "merge_row_data", Mock(side_effect=merge_data.SerialzationError))
    with pytest.raises(merge_data.SerialzationError) as error:
        merge_data.merge_data_from_getmarc(
            io.BytesIO(SAMPLE_MAPPING_FILE_CONTENTS),
            input_metadata_tsv_fp=io.StringIO(SAMPLE_METADATA_TSV_FILE_CONTENTS),
            get_marc_server_strategy=get_marc_server_strategy,
            dialect="excel-tab",
    )
    assert "line 2" in str(error)    # get_marc_server_strategy.assert_called_once_with("dummy_id")


def test_merge_data_from_getmarc_warns_about_extra_mapping_keys(caplog):
    sample_metadata_tsv_file_contents = """
"Uniform Title"	"Bibliographic Identifier"
"spam"	"spam_id"
"bacon"	"bacon_id"
""".lstrip()

    sample_mapping_with_extra_mappings = b"""
[mappings]
identifier_key = "Bibliographic Identifier"  

[[mapping]]
key = "Uniform Title"
matching_marc_fields = []
delimiter = "||"
existing_data = "keep"

[[mapping]]
key = "Some Other Mapping not found in the tsv"
matching_marc_fields = []
delimiter = "||"
existing_data = "keep"
""".lstrip()
    merge_data.merge_data_from_getmarc(
        io.BytesIO(sample_mapping_with_extra_mappings),
        input_metadata_tsv_fp=io.StringIO(sample_metadata_tsv_file_contents),
        get_marc_server_strategy=Mock(return_value="Bacon"),
        dialect="excel-tab",
    )
    assert (
        caplog.records[0].levelname == "WARNING"
        and caplog.records[0].message
        == 'Mapping contains key not found in table: "Some Other Mapping not '
        'found in the tsv"'
    )
    assert len(caplog.records) == 1
    # assert ["Foo"] == [rec.message for rec in caplog.records]


@pytest.mark.parametrize(
    "existing_data, starting_value, expected_value",
    [
        ("replace", "spam", "Bacon"),
        ("keep", "spam", "spam"),
        ("append", "spam", "spam||Bacon"),
        ("replace", "", "Bacon"),
        ("keep", "", "Bacon"),
        ("append", "", "Bacon"),
    ],
)
def test_merge_data_from_getmarc_handles_existing_data(
    existing_data, starting_value, expected_value
):
    mapping_file_contents = f"""
[mappings]
identifier_key = "Bibliographic Identifier"  

[[mapping]]
key = "Uniform Title"
matching_marc_fields = ["120a"]
delimiter = "||"
existing_data = "{existing_data}"
""".lstrip().encode("ascii")

    get_marc_server_strategy = Mock(
        return_value=ET.fromstring(SAMPLE_ALMA_RECORD)
    )

    metadata_tsv_file_contents = f"""
"Uniform Title"	"Bibliographic Identifier"
"{starting_value}"	"dummy_id"
""".lstrip()

    rows = merge_data.merge_data_from_getmarc(
        io.BytesIO(mapping_file_contents),
        input_metadata_tsv_fp=io.StringIO(metadata_tsv_file_contents),
        get_marc_server_strategy=get_marc_server_strategy,
        dialect="excel-tab",
    )
    assert rows == [
        {
            "Bibliographic Identifier": "dummy_id",
            "Uniform Title": expected_value,
        }
    ]


def test_jinja2_template():
    template_string = "{% for field in fields['700'] %}{{ field['a'] }}{% if field['q'] %} {{field['q']}}{%endif%} {{ field['d'] }}{% if not loop.last %}||{% endif %}{% endfor %}"
    template = Template(template_string)
    result = template.render(
        fields={
            "700": [
                {"a": "Shakespeare, William,", "d": "1564-1616"},
                {
                    "a": "Jung, C. G.",
                    "q": "(Carl Gustav),",
                    "d": "1875-1961",
                },
            ]
        }
    )
    assert (
        result
        == "Shakespeare, William, 1564-1616||Jung, C. G. (Carl Gustav), 1875-1961"
    )


def test_merge_data_from_getmarc_handles_invalid_existing_data_value():
    mapping_file_contents = """
    [mappings]
    identifier_key = "Bibliographic Identifier"  
    
    [[mapping]]
    key = "Uniform Title"
    matching_marc_fsyncields = ["120a"]
    delimiter = "||"
    existing_data = "something_invalid"
    """.lstrip().encode("ascii")

    get_marc_server_strategy = Mock(
        return_value=ET.fromstring("""
    <record xmlns="http://www.loc.gov/MARC21/slim" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xsi:schemaLocation="http://www.loc.gov/MARC21/slim 
                                http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd">
    <datafield ind1=" " ind2=" " tag="120">
    <subfield code="a">Bacon</subfield>
    </datafield>
    </record>
    """)
    )

    metadata_tsv_file_contents = """
    "Uniform Title"	"Bibliographic Identifier"
    ""	"dummy_id"
    """.lstrip()
    with pytest.raises(merge_data.BadMappingDataError):
        merge_data.merge_data_from_getmarc(
            io.BytesIO(mapping_file_contents),
            input_metadata_tsv_fp=io.StringIO(metadata_tsv_file_contents),
            get_marc_server_strategy=get_marc_server_strategy,
            dialect="excel-tab",
        )


alma_record_with_multiple_same_letter_codes = """
    <record xmlns="http://www.loc.gov/MARC21/slim" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xsi:schemaLocation="http://www.loc.gov/MARC21/slim 
                                http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd">
        <datafield ind1=" " ind2="0" tag="650">
            <subfield code="a">Toll roads</subfield>
            <subfield code="x">Law and legislation</subfield>
            <subfield code="z">Ireland</subfield>
            <subfield code="z">Dublin</subfield>
            <subfield code="v">Early works to 1800.</subfield>
        </datafield>
        <datafield ind1=" " ind2="0" tag="650">
            <subfield code="a">Highway law</subfield>
            <subfield code="z">Ireland</subfield>
            <subfield code="z">Dublin</subfield>
            <subfield code="v">Early works to 1800.</subfield>
        </datafield>
        <datafield ind1=" " ind2="0" tag="650">
            <subfield code="a">Tolls</subfield>
            <subfield code="z">Ireland</subfield>
            <subfield code="z">Dublin</subfield>
            <subfield code="v">Early works to 1800.</subfield>
        </datafield>
    </record>
    """


def test_organize_with_code_and_value_gets_number_of_fields_right():
    assert (
        len(
            merge_data.organize_with_code_and_value(
                ET.fromstring(alma_record_with_multiple_same_letter_codes)
            )
        )
        == 1
    )


def test_organize_with_code_and_value_gets_number_of_fields_within_a_field_type_right():
    assert (
        len(
            merge_data.organize_with_code_and_value(
                ET.fromstring(alma_record_with_multiple_same_letter_codes)
            )["650"]
        )
        == 3
    )


def test_organize_with_code_and_value_gets_subfields_right():
    assert (
        len(
            merge_data.organize_with_code_and_value(
                ET.fromstring(alma_record_with_multiple_same_letter_codes)
            )["650"][0]
        )
        == 5
    )


def test_organize_with_code_and_value_gets_subfield_code_right():
    assert (
        merge_data.organize_with_code_and_value(
            ET.fromstring(alma_record_with_multiple_same_letter_codes)
        )["650"][0][0]["code"]
        == "a"
    )


@pytest.mark.parametrize(
    "template_string, expected_result",
    [
        (
            """
{% set ns = namespace(values = []) %}
{% for field in fields['650'] %}
{% set ns.values = ns.values + [field | selectattr('code', 'equalto', 'a') | map(attribute='value') | join('||')] %}
{% endfor %}
{{ ns.values | join('||') }}
""".lstrip(),
            "Toll roads||Highway law||Tolls",
        ),
        (
            """
{% set ns = namespace(values = []) %}
{% for field in fields['650'] %}
{% set ns.values = ns.values + [field | selectattr('code', 'equalto', 'z') | map(attribute='value') | join('||')] %}
{% endfor %}
{{ ns.values | unique | join('||') }}
""".lstrip(),
            "Ireland||Dublin",
        ),
    ],
)
def test_field_with_code_and_value(template_string, expected_result):
    alma_record = """
    <record xmlns="http://www.loc.gov/MARC21/slim" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xsi:schemaLocation="http://www.loc.gov/MARC21/slim 
                                http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd">
        <datafield ind1=" " ind2="0" tag="650">
            <subfield code="a">Toll roads</subfield>
            <subfield code="x">Law and legislation</subfield>
            <subfield code="z">Ireland</subfield>
            <subfield code="z">Dublin</subfield>
            <subfield code="v">Early works to 1800.</subfield>
        </datafield>
        <datafield ind1=" " ind2="0" tag="650">
            <subfield code="a">Highway law</subfield>
            <subfield code="z">Ireland</subfield>
            <subfield code="z">Dublin</subfield>
            <subfield code="v">Early works to 1800.</subfield>
        </datafield>
        <datafield ind1=" " ind2="0" tag="650">
            <subfield code="a">Tolls</subfield>
            <subfield code="z">Ireland</subfield>
            <subfield code="z">Dublin</subfield>
            <subfield code="v">Early works to 1800.</subfield>
        </datafield>
    </record>
    """
    assert (
        merge_data.serialize_with_jinja_template(
            marc_record=ET.fromstring(alma_record),
            config=merge_data.MappingConfig(
                key="Name",
                matching_keys=["650"],
                delimiter="||",
                existing_data="replace",
                serialize_method="jinja2template",
                experimental={"jinja2template": {"template": template_string}},
            ),
            enable_experimental_features=True,
        )
        == expected_result
    )

def test_serialize_with_jinja_template_type_error_raise_serialization_error(monkeypatch):
    config = Mock(
        serialize_method="jinja2template",
        experimental={
            "jinja2template": {
                'template': ""
            }
        }
    )
    monkeypatch.setattr(
        merge_data.jinja2.Template,
        "render",
        Mock(
            name="render",
            side_effect=TypeError(
                'can only concatenate list (not "str") to list'
            )
        )
    )
    with pytest.raises(merge_data.SerialzationError):
        merge_data.serialize_with_jinja_template(marc_record=MagicMock(), config=config, enable_experimental_features=True)

def test_get_matching_marc_data():
    request_strategy = Mock(return_value=Mock(text="<spam></spam>"))
    merge_data.get_matching_marc_data(
        mmsid="12344556677",
        get_marc_server="https://spamserver",
        request_strategy=request_strategy,
    )
    request_strategy.assert_called_once_with(
        "https://spamserver/api/record?mms_id=12344556677"
    )


def test_write_new_rows_to_file():
    data = io.StringIO()
    rows = [{"header1": "value1", "header2": "value2"}]
    merge_data.write_new_rows_to_file(rows, "excel-tab", data)
    results = data.getvalue()
    assert "header1\theader2" in results


@pytest.mark.parametrize(
    "config, expected_value",
    [
        (
            merge_data.MappingConfig(
                key="Uniform Title",
                matching_keys=["120a"],
                delimiter="||",
                existing_data="keep",
            ),
            "Bacon",
        ),
        (
            merge_data.MappingConfig(
                key="Uniform Title",
                matching_keys=["120b"],
                delimiter="||",
                existing_data="keep",
            ),
            None,
        ),
        (
            merge_data.MappingConfig(
                key="Uniform Title",
                matching_keys=["040d"],
                delimiter="||",
                existing_data="keep",
            ),
            "TJC||OCLCQ||OCLCG||OCLCF||OCLCO||OCLCA",
        ),
    ],
)
def test_locate_marc_value_in_record(config, expected_value):
    assert (
        merge_data.locate_marc_value_in_record(
            config, ET.fromstring(SAMPLE_ALMA_RECORD)
        )
        == expected_value
    )


# def test_locate_marc_value_in_record_bad_data():
#     invalid_record = ET.fromstring('''<record xmlns="http://www.loc.gov/MARC21/slim"
#         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
#         xsi:schemaLocation="http://www.loc.gov/MARC21/slim
#                             http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd">
# <datafield ind1=" " ind2=" " tag="120">
# <subfield code="a">Bacon</subfield>
# <subfield code="c">Eggs</subfield>
# </datafield>
# <datafield ind1=" " ind2=" " tag="040">
# </datafield>
# </record>
# '''.lstrip())
#     config = merge_data.MappingConfig(
#         key="Uniform Title",
#         matching_marc_fields=["040d"],
#         delimiter="||",
#         existing_data="keep"
#     )
#     with pytest.raises(ValueError):
#         merge_data.locate_marc_value_in_record(config, invalid_record)
def test_map_marc_mapping_to_mapping_config_is_mapping_config():
    mapping_data = {
        "key": "Uniform Title",
        "matching_marc_fields": ["120a"],
        "delimiter": "||",
        "existing_data": "keep",
    }
    assert isinstance(
        merge_data.map_marc_mapping_to_mapping_config(mapping_data),
        merge_data.MappingConfig,
    )


@pytest.mark.parametrize(
    "attribute, expected_value",
    [
        ("key", "Uniform Title"),
        ("matching_keys", ["120a"]),
        ("delimiter", "||"),
        ("existing_data", "keep"),
    ],
)
def test_map_marc_mapping_to_mapping_config(attribute, expected_value):
    result = merge_data.map_marc_mapping_to_mapping_config(
        {
            "key": "Uniform Title",
            "matching_marc_fields": ["120a"],
            "delimiter": "||",
            "existing_data": "keep",
        },
        validations=[],
    )
    assert getattr(result, attribute) == expected_value


def test_map_marc_mapping_to_mapping_config_invalid():
    with pytest.raises(merge_data.BadMappingDataError):
        merge_data.map_marc_mapping_to_mapping_config(
            {
                "key": "Uniform Title",
                "matching_marc_fields": ["120a"],
                "delimiter": "||",
                "existing_data": "something_invalid",
            },
            validations=[lambda *args: "something_invalid"],
        )


def test_validate_is_not_list_found_issue():
    assert (
        merge_data.validate_is_not_list({"key": ["Uniform Title"]}, "key")
        is not None
    )


def test_validate_is_not_list_found_no_issue():
    assert (
        merge_data.validate_is_not_list({"key": "Uniform Title"}, "key")
        is None
    )


def test_validate_is_list_found_no_issues():
    assert (
        merge_data.validate_is_list_of_strings(
            {"key": ["Uniform Title"]}, "key"
        )
        is None
    )


def test_validate_is_list_found_issue_not_being_a_list():
    assert (
        merge_data.validate_is_list_of_strings({"key": "Uniform Title"}, "key")
        is not None
    )


def test_validate_is_list_found_issue_with_not_contain_strings():
    assert (
        merge_data.validate_is_list_of_strings({"key": [1, 2]}, "key")
        is not None
    )


def test_validate_is_string_found_no_issues():
    assert (
        merge_data.validate_is_string({"key": "Uniform Title"}, "key") is None
    )


def test_validate_is_string_found_issue():
    assert merge_data.validate_is_string({"key": 1}, "key") is not None


def test_read_mapping_toml_data_invalid_toml_raises_BadMappingFileError():
    d = io.BytesIO()
    d.write(
        """
[mappings]

identifier_key = "Local Bib ID
"

""".lstrip().encode("utf-8")
    )
    d.seek(0)
    with pytest.raises(merge_data.BadMappingDataError) as e:
        merge_data.read_mapping_toml_data(d)
    assert "Illegal character '\\n'" in e.value.details


def test_row_merge_data_strategy_bad_mapping_data_source(fs):
    fs.create_file(os.path.join("fake_data", "input_metadata_tsv_file.tsv"))
    input_metadata_tsv_file = pathlib.Path(
        os.path.join("fake_data", "input_metadata_tsv_file.tsv")
    )
    data = """
    [mappings]
    
    identifier_key = "Local Bib ID
    "
    
    """.lstrip()
    fs.create_file(
        os.path.join("fake_data", "mapping_file.toml"), contents=data
    )
    mapping_file = pathlib.Path(os.path.join("fake_data", "mapping_file.toml"))
    with pytest.raises(merge_data.BadMappingFileError) as error:
        merge_data.merge_from_getmarc(
            input_metadata_tsv_file=input_metadata_tsv_file,
            output_metadata_tsv_file=Mock(),
            mapping_file=mapping_file,
            get_marc_server=Mock(),
        )
    assert error.value.source == mapping_file


def test_row_merge_data_strategy_bad_mapping_data_details(fs):
    fs.create_file(os.path.join("fake_data", "input_metadata_tsv_file.tsv"))
    input_metadata_tsv_file = pathlib.Path(
        os.path.join("fake_data", "input_metadata_tsv_file.tsv")
    )
    data = """
    [mappings]
    
    identifier_key = "Local Bib ID
    "
    
    """.lstrip()
    fs.create_file(
        os.path.join("fake_data", "mapping_file.toml"), contents=data
    )
    with pytest.raises(merge_data.BadMappingFileError) as error:
        merge_data.merge_from_getmarc(
            input_metadata_tsv_file=input_metadata_tsv_file,
            output_metadata_tsv_file=Mock(),
            mapping_file=pathlib.Path(
                os.path.join("fake_data", "mapping_file.toml")
            ),
            get_marc_server=Mock(),
        )
    assert error.value.details is not None


class TestBadMappingFileError:
    def test_str_with_no_details(self):
        with pytest.raises(merge_data.BadMappingFileError) as e:
            raise merge_data.BadMappingFileError(
                pathlib.Path(os.path.join("fake_data", "mapping_file.toml"))
            )
        assert os.path.join("fake_data", "mapping_file.toml") in str(e.value)

    def test_str_with_details(self):
        with pytest.raises(merge_data.BadMappingFileError) as e:
            raise merge_data.BadMappingFileError(
                source_file=pathlib.Path(
                    os.path.join("fake_data", "mapping_file.toml")
                ),
                details="something bad",
            )
        assert all([
            os.path.join("fake_data", "mapping_file.toml") in str(e.value),
            "something bad" in str(e.value),
        ]), f"expected both file name and error message, got: {e.value}"
