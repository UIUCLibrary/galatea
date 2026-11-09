"""Convert qmllint report to something that jenkins can parse by Warnings."""

import argparse
import pprint

# it needs to look like this https://github.com/jenkinsci/warnings-ng-plugin/blob/main/plugin/src/test/resources/io/jenkins/plugins/analysis/warnings/steps/issues.json
import json

__all__ = []

import sys

QMLLINT_TO_JENKINS_SEVERITY_MAP = {
    "error": "ERROR",
    "warning": "NORMAL",
    "info": "NORMAL",
}


def get_arg_parsers():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="Input qmllint report json file")
    parser.add_argument("--output-file", help="output file")
    return parser


def create_jenkins_report(input_file):
    with open(input_file, "r") as f:
        data = json.load(f)
        for file_item in data["files"]:
            if file_item["success"]:
                continue
            for warning in file_item.get("warnings", []):
                suggestions = [
                    suggestion["message"]
                    for suggestion in warning.get("suggestions", [])
                ]
                try:
                    results = {
                        "fileName": file_item["filename"],
                        "message": warning["message"],
                        "lineStart": warning["line"],
                        "lineEnd": warning["line"] + 1,
                        "category": warning["id"],
                        "columnStart": warning["column"],
                        "columnEnd": warning["column"] + warning["length"],
                        "severity": QMLLINT_TO_JENKINS_SEVERITY_MAP[
                            warning["type"]
                        ],
                    }
                    if suggestions := warning.get("suggestions", []):
                        results["description"] = "\n".join([
                            suggestion["message"] for suggestion in suggestions
                        ])
                    yield results
                except KeyError as e:
                    pprint.pprint(file_item)
                    raise e


def main():
    args = get_arg_parsers().parse_args()

    output_data = create_jenkins_report(args.input_file)
    if args.output_file:
        with open(args.output_file, "w", encoding="utf-8") as f:
            for line in output_data:
                f.write(json.dumps(line) + "\n")
        print(f"Wrote report to {args.output_file}", file=sys.stderr)
    else:
        for line in output_data:
            print(json.dumps(line))


if __name__ == "__main__":
    main()
