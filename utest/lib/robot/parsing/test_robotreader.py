from robotide.lib.robot.parsing.robotreader import RobotReader


def test_reads_two_space_separators_when_four_spaces_are_configured():
    reader = RobotReader(spaces=4, lang=["en"])
    assert reader._spaces == 4
    reader.check_separator("*** Test Cases ***")
    assert reader._cell_section is True
    assert reader._separator_check is False
    reader.check_separator("First test case")
    row = "  Keyword with two arguments  arg1  arg2"

    reader.check_separator(row)
    assert reader._spaces == 2
    assert reader._separator_check is True

    assert reader.split_row(row) == [
        "",
        "Keyword with two arguments",
        "arg1",
        "arg2",
    ]

    reader.check_separator("*** Keywords ***")
    assert reader._cell_section is True
    assert reader._separator_check is False
    reader.check_separator("Bad Spacing Keyword")
    row = "      Log      Content      console=True"

    reader.check_separator(row)
    assert reader._separator_check is True
    assert reader._spaces == 6
    assert reader.split_row(row) == [
        "",
        "Log",
        "Content",
        "console=True",
    ]