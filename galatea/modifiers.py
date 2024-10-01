
def remove_duplicates(entry: str) -> str:
    values = entry.split("||")
    new_values = []
    for value in values:
        if value in new_values:
            continue
        new_values.append(value)

    return "||".join(new_values)


def remove_trailing_periods(entry: str) -> str:
    values = entry.split("||")
    new_values = []
    for value in values:
        if value.endswith("."):
            new_values.append(value[:-1])
        else:
            new_values.append(value)
    return "||".join(new_values)


def remove_double_dash_postfix(entry: str) -> str:
    values = entry.split("||")
    new_values = []
    for value in values:
        if "--" in value:
            index = value.find("--")
            new_values.append(value[:index])
        else:
            new_values.append(value)

    return "||".join(new_values)
