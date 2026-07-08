import pytest
from unittest.mock import Mock


sw_workflows = pytest.importorskip("galatea.gui.workflows")


@pytest.mark.parametrize(
    "workflow_klass",
    [
        sw_workflows.AuthorizedTermsCheck,
        sw_workflows.CleanTsv,
        sw_workflows.GetMarcInitMapper,
        sw_workflows.GetMarcMerge,
        sw_workflows.NewTransformationFile,
        sw_workflows.ResolveAuthorizedTerms,
    ],
)
def test_all_workflows_have_name(workflow_klass):
    assert hasattr(workflow_klass(), "name")


@pytest.mark.parametrize(
    "workflow_klass,results, user_args",
    [
        (sw_workflows.AuthorizedTermsCheck, [], {}),
        (sw_workflows.CleanTsv, [], {}),
        (
            sw_workflows.GetMarcInitMapper,
            [Mock(data={"new_toml_file": "somefile.toml"})],
            {},
        ),
        (sw_workflows.GetMarcMerge, [], {"Output .tsv": "output.tsv"}),
        (sw_workflows.NewTransformationFile, [], {}),
        (sw_workflows.ResolveAuthorizedTerms, [], {}),
    ],
)
def test_all_workflows_have_produce_some_report(
    workflow_klass, results, user_args
):
    assert workflow_klass.generate_report(results, user_args)


@pytest.mark.parametrize(
    "workflow_klass, initial_results, additional_data, user_args, workflow_configuration, expected",
    [
        (
            sw_workflows.AuthorizedTermsCheck,
            [],
            {},
            {"Source .tsv": "input.tsv"},
            {},
            [{"source": "input.tsv"}],
        ),
        (
            sw_workflows.CleanTsv,
            [],
            {},
            {"Source .tsv": "input.tsv"},
            {},
            [{"source": "input.tsv", "destination": "input.tsv"}],
        ),
        (
            sw_workflows.GetMarcInitMapper,
            [],
            {},
            {
                "Source .tsv": "input.tsv",
                "Output mapper toml file": "out.toml",
            },
            {},
            [{"source": "input.tsv", "output": "out.toml"}],
        ),
        (
            sw_workflows.GetMarcMerge,
            [],
            {},
            {
                "Source metadata .tsv file": "source.tsv",
                "Mapper .toml file": "mapper.toml",
                "Output .tsv": "output.tsv",
            },
            {"GetMarc Server Url": "https://fake.com"},
            [
                {
                    "get_marc_url": "https://fake.com",
                    "mapper_toml": "mapper.toml",
                    "output_tsv": "output.tsv",
                    "source_tsv": "source.tsv",
                }
            ],
        ),
        (
            sw_workflows.NewTransformationFile,
            [],
            {},
            {"File Name": "output.toml"},
            {},
            [{"output": "output.toml"}],
        ),
        (
            sw_workflows.ResolveAuthorizedTerms,
            [],
            {},
            {
                "Source .tsv": "source.tsv",
                "Transformation .tsv file": ".tsv",
                "Output .tsv": "output.tsv",
            },
            {},
            [
                {
                    "output_file": "output.tsv",
                    "source_file": "source.tsv",
                    "transformer_file": ".tsv",
                }
            ],
        ),
    ],
)
def test_all_workflows_discover_task_metadata(
    workflow_klass,
    initial_results,
    additional_data,
    user_args,
    workflow_configuration,
    expected,
):
    workflow = workflow_klass()
    backend = Mock(
        get=lambda key: workflow_configuration[key],
    )
    workflow.set_options_backend(backend)
    assert (
        workflow.discover_task_metadata(
            initial_results,
            additional_data=additional_data,
            user_args=user_args,
        )
        == expected
    )


@pytest.mark.parametrize(
    "workflow_klass, args",
    [
        (sw_workflows.AuthorizedTermsCheck, {"source": "input.tsv"}),
        (
            sw_workflows.CleanTsv,
            {"source": "input.tsv", "destination": "output.tsv"},
        ),
        (
            sw_workflows.GetMarcInitMapper,
            {"source": "input.tsv", "output": "output.tsv"},
        ),
        (
            sw_workflows.GetMarcMerge,
            {
                "get_marc_url": "https://fake.com",
                "source_tsv": "source.tsv",
                "mapper_toml": "mapper.toml",
                "output_tsv": "output.tsv",
            },
        ),
        (sw_workflows.NewTransformationFile, {"output": "mapper.toml"}),
        (sw_workflows.ResolveAuthorizedTerms, {"source_file": "source.tsv"}),
    ],
)
def test_all_workflows_create_at_lease_one_task(workflow_klass, args):
    task_builder = Mock()
    workflow = workflow_klass()
    workflow.create_new_task(task_builder, args)
    task_builder.add_subtask.assert_called()


@pytest.mark.parametrize(
    "workflow_klass",
    [
        sw_workflows.AuthorizedTermsCheck,
        sw_workflows.CleanTsv,
        sw_workflows.GetMarcInitMapper,
        sw_workflows.GetMarcMerge,
        sw_workflows.NewTransformationFile,
        sw_workflows.ResolveAuthorizedTerms,
    ],
)
def test_all_workflows_have_descriptions(workflow_klass):
    assert hasattr(workflow_klass(), "description")


class TestAuthorizedTermsCheck:
    @pytest.mark.parametrize(
        "value, findings",
        [
            ("dummy.tsv", []),
            ("dummy.toml", ["File must be a .tsv file"]),
            ("", ["Value is empty"]),
        ],
    )
    def test_job_args_source_tsv(self, value, findings):
        workflow = sw_workflows.AuthorizedTermsCheck()
        options = workflow.job_options()
        source_tsv_option = options[0]
        assert source_tsv_option.label == "Source .tsv"
        source_tsv_option.value = value
        assert source_tsv_option.get_findings() == findings


class TestNewTransformationFile:
    @pytest.mark.parametrize(
        "arg_position, expected_label, value, findings",
        [
            (0, "File Name", "output.tsv", []),
            (0, "File Name", "output.txt", ["File must be a .tsv file"]),
        ],
    )
    def test_job_args(self, arg_position, expected_label, value, findings):
        workflow = sw_workflows.NewTransformationFile()
        option = workflow.job_options()[arg_position]
        assert option.label == expected_label
        option.value = value
        assert option.get_findings() == findings


class TestResolveAuthorizedTerms:
    @pytest.mark.parametrize(
        "arg_position, expected_label, value, findings",
        [
            (0, "Source .tsv", "input.tsv", []),
            (0, "Source .tsv", "input.txt", ["File must be a .tsv file"]),
            (1, "Transformation .tsv file", "input.tsv", []),
            (
                1,
                "Transformation .tsv file",
                "input.txt",
                ["File must be a .tsv file"],
            ),
            (2, "Output .tsv", "output.tsv", []),
            (2, "Output .tsv", "ouput.txt", ["File must be a .tsv file"]),
        ],
    )
    def test_job_args(self, arg_position, expected_label, value, findings):
        workflow = sw_workflows.ResolveAuthorizedTerms()
        option = workflow.job_options()[arg_position]
        assert option.label == expected_label
        option.value = value
        assert option.get_findings() == findings


class TestGetMarcMerge:
    @pytest.mark.parametrize(
        "arg_position, expected_label, value, findings",
        [
            (0, "Source metadata .tsv file", "input.tsv", []),
            (
                0,
                "Source metadata .tsv file",
                "input.txt",
                ["File must be a .tsv file"],
            ),
            (1, "Mapper .toml file", "input.toml", []),
            (
                1,
                "Mapper .toml file",
                "input.tsv",
                ["File must be a .toml file"],
            ),
            (2, "Output .tsv", "output.tsv", []),
            (2, "Output .tsv", "output.txt", ["File must be a .tsv file"]),
        ],
    )
    def test_job_args(self, arg_position, expected_label, value, findings):
        workflow = sw_workflows.GetMarcMerge()
        option = workflow.job_options()[arg_position]
        assert option.label == expected_label
        option.value = value
        assert option.get_findings() == findings


class TestGetMarcInitMapper:
    @pytest.mark.parametrize(
        "arg_position, expected_label, value, findings",
        [
            (0, "Source .tsv", "input.tsv", []),
            (0, "Source .tsv", "input.txt", ["File must be a .tsv file"]),
            (1, "Output mapper toml file", "output.toml", []),
            (
                1,
                "Output mapper toml file",
                "output.tsv",
                ["File must be a .toml file"],
            ),
        ],
    )
    def test_job_args(self, arg_position, expected_label, value, findings):
        workflow = sw_workflows.GetMarcInitMapper()
        option = workflow.job_options()[arg_position]
        assert option.label == expected_label
        option.value = value
        assert option.get_findings() == findings


class TestCleanTsv:
    @pytest.mark.parametrize(
        "arg_position, expected_label, value, findings",
        [
            (0, "Source .tsv", "input.tsv", []),
            (0, "Source .tsv", "input.txt", ["File must be a .tsv file"]),
        ],
    )
    def test_job_args(self, arg_position, expected_label, value, findings):
        workflow = sw_workflows.CleanTsv()
        option = workflow.job_options()[arg_position]
        assert option.label == expected_label
        option.value = value
        assert option.get_findings() == findings
