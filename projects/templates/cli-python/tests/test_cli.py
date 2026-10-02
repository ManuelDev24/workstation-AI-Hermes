from mycli.main import main


def test_count(tmp_path, capsys):
    f = tmp_path / "a.txt"
    f.write_text("hola mundo\notra linea\n")
    assert main([str(f), "--solo", "palabras"]) == 0
    assert capsys.readouterr().out.strip() == "4"


def test_missing_file_exit_2(tmp_path, capsys):
    assert main([str(tmp_path / "x.txt")]) == 2
    assert "error" in capsys.readouterr().err
