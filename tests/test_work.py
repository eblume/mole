from pytest import CaptureFixture

from mole.work import work


def test_all_done(capsys: CaptureFixture):
    work()
    captured = capsys.readouterr()
    assert captured.out.endswith("All Done!\n")
