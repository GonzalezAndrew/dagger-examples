from src.main import main

def test_main():
    expected = 0
    result = main()
    assert expected == result


def test_main_fail():
    failure = 1
    result = main()
    assert failure != result
