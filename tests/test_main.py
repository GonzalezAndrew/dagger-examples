from src.main import main

def test_main():
    expected = 0
    result = main()
    assert expected == result
