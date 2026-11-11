"""Süreç Uzmanı and Sayısal Tasarım Uzmanı on the same computer at the same time. Both are built from the same
source, so everything one app could find of the other must carry Süreç Uzmanı's own name: the app folders (settings,
API keys, library, chats, log, WebView2 data, single-instance key and port), the Windows names (mutex, icon window
class, activation message), the environment variables, the organization settings file in a shared folder, and the
icon's place on the screen."""

import yaml

from techrag import launcher as L
from techrag import org
from techrag.config import APP_NAME, ENV_PREFIX, app_dir, load_config
from techrag.launcher import Monitor, place

# What Sayısal Tasarım Uzmanı uses (its source as copied into this repository, 0.15.3).
STU_FOLDERS = ("SayisalTasarimUzmani", "TechRAG")
STU_INTERNAL_PREFIX = "TechRAG"
STU_ENV_PREFIX = "TECHRAG_"
STU_ORG_FILE = "kurum-ayarlari.yaml"
STU_ICON_ANCHOR = {"h": "right", "dx": 16, "v": "bottom", "dy": 16}

FHD = Monitor("\\\\.\\DISPLAY1", (0, 0, 1920, 1080), (0, 0, 1920, 1040), 96, True)
HIDPI = Monitor("\\\\.\\DISPLAY1", (0, 0, 2880, 1620), (0, 0, 2880, 1560), 144, True)


def test_the_app_folder_is_its_own_never_the_sayisal_tasarim_uzmani_ones(tmp_path):
    assert app_dir(tmp_path).name == "SurecUzmani"
    assert app_dir(tmp_path, lower=True).name == "surecuzmani"
    for other in STU_FOLDERS:
        (tmp_path / other).mkdir()
        (tmp_path / other.lower()).mkdir(exist_ok=True)
    assert app_dir(tmp_path).name == "SurecUzmani", "settings, keys and library are not shared with the other app"
    assert app_dir(tmp_path, lower=True).name == "surecuzmani"


def test_internal_windows_names_differ_from_sayisal_tasarim_uzmani():
    names = [L.ACTIVATE_MESSAGE, L.Launcher.class_name("k"), f"{L.INTERNAL_PREFIX}.k"]   # last: the mutex name
    assert all(n.startswith(f"{APP_NAME}.") for n in names), names
    assert not any(n.startswith(f"{STU_INTERNAL_PREFIX}.") for n in names)


def test_sayisal_tasarim_uzmani_environment_variables_are_not_read(monkeypatch, tmp_path):
    assert ENV_PREFIX == "SURECUZMANI_" != STU_ENV_PREFIX
    stu_config = tmp_path / "stu.yaml"
    stu_config.write_text(yaml.safe_dump({"llm": {"model": "stu-config-model"}}), encoding="utf-8")
    monkeypatch.setenv(f"{STU_ENV_PREFIX}CONFIG", str(stu_config))
    monkeypatch.setenv(f"{STU_ENV_PREFIX}LLM__MODEL", "stu-model")
    monkeypatch.setenv(f"{STU_ENV_PREFIX}RERANKER__MODEL", "stu-reranker")
    cfg = load_config()
    assert cfg.llm.model not in ("stu-model", "stu-config-model") and cfg.reranker.model != "stu-reranker"
    monkeypatch.setenv(f"{ENV_PREFIX}LLM__MODEL", "own-model")
    assert load_config().llm.model == "own-model", "the app's own variables still work"


def test_sayisal_tasarim_uzmani_organization_settings_variable_is_not_read(monkeypatch, tmp_path):
    share = tmp_path / "share"
    share.mkdir()
    (share / STU_ORG_FILE).write_text(yaml.safe_dump({"llm": {"model": "stu-model"}}), encoding="utf-8")
    monkeypatch.setenv(f"{STU_ENV_PREFIX}ORG_SETTINGS", str(share))   # e.g. given to every PC by group policy
    assert org.locate({}) == (None, "")
    monkeypatch.setenv(f"{ENV_PREFIX}ORG_SETTINGS", str(share))
    assert org.locate({}) == (share / "SurecUzmani.kurum-ayarlari.yaml", "env")


def test_one_shared_folder_holds_both_apps_organization_settings(tmp_path):
    """An admin may pick the same network folder for both apps: each writes and reads only its own file."""
    from techrag.config import Config

    share = tmp_path / "share"
    share.mkdir()
    stu_text = "# Sayısal Tasarım Uzmanı - kurum ayarları\nllm:\n  model: stu-model\n"
    (share / STU_ORG_FILE).write_text(stu_text, encoding="utf-8")
    assert org.ORG_FILE != STU_ORG_FILE and org.org_file(share).name == org.ORG_FILE
    cfg = Config()
    cfg.llm.model = "surec-model"
    out = org.save(share, cfg)
    assert out["file"] == str(share / org.ORG_FILE)
    assert (share / STU_ORG_FILE).read_text(encoding="utf-8") == stu_text, "the other app's file is untouched"
    assert yaml.safe_load((share / org.ORG_FILE).read_text(encoding="utf-8"))["llm"]["model"] == "surec-model"
    assert "stu-model" not in str(org.load({"org": {"path": str(share)}}))


def test_the_icon_starts_next_to_sayisal_tasarim_uzmani_s_never_on_it():
    for mon in (FHD, HIDPI):
        _, sx, sy, ss = place(STU_ICON_ANCHOR, [mon])      # where the other app's icon starts
        _, x, y, s = place(None, [mon])                     # where this app's icon starts
        assert s == ss and y == sy, "same row, same size"
        assert x + s < sx, "to the left of it, not overlapping"
        assert sx - (x + s) == round(L.SIBLING_GAP_DIP * mon.scale)
        assert mon.work[2] - (x + s) == round(L.DEFAULT_DX_DIP * mon.scale)
