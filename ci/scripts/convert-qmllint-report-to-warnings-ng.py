# it needs to look like this https://github.com/jenkinsci/warnings-ng-plugin/blob/main/plugin/src/test/resources/io/jenkins/plugins/analysis/warnings/steps/issues.json
import pprint
import sys

import json


def main():
    output_data = {
        "_class": "io.jenkins.plugins.analysis.core.restapi.ReportApi",
        "issues": [],
        "size": 0,
    }

    with open(sys.argv[1], "r") as f:
        data = json.load(f)
        for file_item in data["files"]:
            if file_item["success"]:
                continue
            for warning in file_item.get("warnings", []):
                # print(warning)
                try:
                    output_data["issues"].append({
                        "fileName": file_item["filename"],
                        "message": warning["message"],
                        "lineStart": warning["line"],
                        "category": warning["id"],
                        "columnStart": warning["column"],
                        "severity": warning["type"],
                    })
                except KeyError as e:
                    pprint.pprint(file_item)
                    raise e
    print(json.dumps(output_data))


if __name__ == "__main__":
    main()
