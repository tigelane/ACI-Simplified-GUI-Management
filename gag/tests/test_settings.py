import pytest
from Settings.Settings import Settings, SettingsError
import yaml


def test_settings_initialize_with_no_yaml_file():
    Settings()


def test_settings_initialize_with_yaml_file(tmp_path):
    test_content = {'setting1': 'data1', 'setting2': 'data2'}
    test_yaml = yaml.dump(test_content)
    tmp_file = tmp_path / "settings.yml"
    tmp_file.write_text(test_yaml)

    s = Settings(tmp_file)
    print(dir(s))
    assert hasattr(s, 'setting1')
    assert hasattr(s, 'setting2')
    assert s.setting1 == 'data1'
    assert s.setting2 == 'data2'


def test_settings_initialize_with_malformed_file(tmp_path):
    bad_yaml = "setting1:\n  subsetting1: bad_yaml: should_be_quoted\n  subsetting2: data2\nsetting2: data2\n"
    tmp_file = tmp_path / "settings.yml"
    tmp_file.write_text(bad_yaml)

    with pytest.raises(SettingsError) as e:
        Settings(tmp_file)

    assert "You have a malformed 'settings.yml' file" in str(e.value)
