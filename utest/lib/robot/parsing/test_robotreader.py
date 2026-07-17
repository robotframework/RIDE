from robotide.lib.robot.parsing.robotreader import RobotReader


def test_reads_two_space_separators_when_four_spaces_are_configured():
    reader = RobotReader(spaces=4, lang=["en"])
    reader.check_separator("*** Test Cases ***")
    reader.check_separator("First test case")
    row = "    Keyword with two arguments  arg1  arg2"

    reader.check_separator(row)

    assert reader.split_row(row) == [
        "",
        "Keyword with two arguments",
        "arg1",
        "arg2",
    ]
