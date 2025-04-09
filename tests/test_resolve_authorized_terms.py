import pathlib

import galatea


# def test_resolve_authorized_terms():
    # Test the resolve_authorized_terms function
    # input_tsv = pathlib.Path("tests/test_data/resolve_authorized_terms_input.tsv")
    # transformation_file = pathlib.Path(
    #     "tests/test_data/resolve_authorized_terms_transformation.tsv"
    # )
    # # output_tsv = pathlib.Path("tests/test_data/resolve_authorized_terms_output.tsv")
    #
    # # Call the function
    # galatea.resolve_authorized_terms(input_tsv, transformation_file)
    # #
    # # # Read the output TSV file
    # # with open(output_tsv, "r") as f:
    # #     output_lines = f.readlines()
    # #
    # # # Check the output lines against expected values
    # # expected_lines = [
    # #     "260$a\t264$a\n",
    # #     "Authorized Term 1\tAuthorized Term 2\n",
    # #     "Authorized Term 3\tAuthorized Term 4\n",
    # # ]
    # # assert output_lines == expected_lines