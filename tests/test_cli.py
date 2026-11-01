from dungeon.cli import main, play
from dungeon.game import Game
from dungeon.render import draw


def test_draw_contains_player_and_status():
    g = Game.new(1)
    text = draw(g, colour=False)
    assert "@" in text
    assert "Depth 1/5" in text
    assert "\033[" not in text
    assert "\033[" in draw(g, colour=True)


def test_play_reads_commands_until_quit():
    g = Game.new(2)
    inputs = iter(["dd", "", "q"])
    out = []
    play(g, read=lambda _: next(inputs), write=lambda *a, **k: out.append(" ".join(map(str, a))),
         colour=False, clear=False)
    assert g.turn >= 1
    assert "Bye!" in out[-1]


def test_play_stops_on_eof_and_reports_death():
    g = Game.new(2)
    g.player.hp = 0
    out = []
    play(g, read=lambda _: (_ for _ in ()).throw(EOFError), write=lambda *a, **k: out.append(str(a)),
         colour=False, clear=False)
    assert "GAME OVER" in out[-1]


def test_play_handles_eof():
    g = Game.new(2)

    def eof(_):
        raise EOFError

    out = []
    play(g, read=eof, write=lambda *a, **k: out.append(str(a)), colour=False, clear=False)
    assert "Bye!" in out[-1]


def test_main_runs_with_piped_input(monkeypatch, capsys):
    inputs = iter(["d", "q"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    assert main(["--seed", "1", "--no-colour"]) == 0
    assert "score" in capsys.readouterr().out
