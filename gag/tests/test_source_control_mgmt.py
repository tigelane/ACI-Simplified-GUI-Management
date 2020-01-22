from SourceControlMgmt import SourceControlMgmt
from SourceControlMgmt.SourceControlMgmt import (SCMCredentialValidationError, SCMCloneRepoError,
                                                 SCMCreateBranchError, SCMWriteFileError,
                                                 SCMPushDataError, SCMDeleteRepoError)

import pytest
import subprocess
import yaml
import pathlib


@pytest.fixture
def setup(tmp_path):
    class Mock_run_return():
        def __init__(self, returncode, out, err):
            self.returncode = returncode
            self.stdout = out
            self.stderr = err

    class Setup():
        def __init__(self):
            self.user = 'fake',
            self.friendly = 'Fake User',
            self.email = 'fake@user.com',
            self.pwd = 'fake_password'
            self.path = tmp_path
            self.repo = "pge-aci-epgs"
            self.branch = "new_branch"
            self.valid_data = {
                "schema": "ent-prod-m1",
                "template": "prod-m1",
                "epgname": "10.153.132"
            }

            self.invalid_data = {
                "template": "prod-m1"
            }

        def mock_fail_with_push_during_push(self, *args, **kwargs):
            if "push" in args[0]:
                return Mock_run_return(128, b"", b"it failed")
            else:
                return Mock_run_return(0, b"it passed", b"")

        def mock_fail_with_push_during_commit(self, *args, **kwargs):
            if "commit" in args[0]:
                return Mock_run_return(128, b"", b"it failed")
            else:
                return Mock_run_return(0, b"it passed", b"")

        def mock_fail_with_push_during_add(self, *args, **kwargs):
            if "add" in args[0]:
                return Mock_run_return(128, b"", b"it failed")
            else:
                return Mock_run_return(0, b"it passed", b"")

        def make_repo_directory(self):
            repo = self.path / self.repo
            data_folder = repo / "test_file"
            data_folder.mkdir(parents=True, exist_ok=False)
            return repo

        def mock_success_return(self, *args, **kwargs):
            return Mock_run_return(0, b"it passed", b"")

        def mock_success_return_clone_repo(self, *args, **kwargs):
            return Mock_run_return(0, b"HEAD is in return value", b"")

        def mock_fail_return(self, *args, **kwargs):
            return Mock_run_return(128, b"", b"it failed")

        def mock_success_clone_repo(self, *args, **kwargs):
            repo = self.path / self.repo
            repo.mkdir(exist_ok=True)
            expected_value = f"Cloning into '{self.path}/{self.repo}'...\n"
            return Mock_run_return(0, b"", expected_value.encode())

        def mock_new_branch_success(self, *args, **kwargs):
            expected_value = f"Switched to a new branch '{self.branch}'\n"
            return Mock_run_return(0, b"", expected_value.encode())

        def remove_yaml_files(self, data, outfile, *args, **kwargs):
            p = pathlib.Path(outfile.name)
            p.unlink()

        def raise_exception(self, *args, **kwargs):
            raise Exception("an exception from testing was raised")

    yield Setup()


@pytest.fixture
def scm(setup):
    scm = SourceControlMgmt.SourceControlMgmt(username=setup.user,
                                              friendly_name=setup.friendly,
                                              email=setup.email,
                                              password=setup.pwd,
                                              repo_name=setup.repo)

    yield scm


def test_create_object_no_parameters():
    expected_value = "All values must have data.  The following attributes are empty: ['username', 'password', 'friendly_name', 'email', 'repo_name']"
    with pytest.raises(TypeError) as e:
        SourceControlMgmt.SourceControlMgmt()

    assert str(e.value) == expected_value


def test_create_object_missing_password(setup):
    expected_value = "All values must have data.  The following attributes are empty: ['password']"
    with pytest.raises(TypeError) as e:
        # Not passing in password
        SourceControlMgmt.SourceControlMgmt(username=setup.user, friendly_name=setup.friendly, email=setup.email, repo_name=setup.repo)
    assert str(e.value) == expected_value


def test_create_object_all_items_present(setup, scm):
    assert isinstance(scm, SourceControlMgmt.SourceControlMgmt)


def test_validate_scm_creds_with_invalid_creds(setup, monkeypatch, scm):
    # Set the mock fail value
    monkeypatch.setattr(subprocess, "run", setup.mock_fail_return)

    with pytest.raises(SCMCredentialValidationError) as e:
        scm.validate_scm_creds()

    assert str(e.value) == "The supplied credentials do not provide access to the given repo"


def test_validate_scm_creds_with_valid_creds(setup, monkeypatch, scm):
    # Set the mock succeed
    monkeypatch.setattr(subprocess, "run", setup.mock_success_return_clone_repo)

    rv = scm.validate_scm_creds()
    assert rv is True


def test_clone_private_repo(setup, monkeypatch, scm):
    monkeypatch.setattr(subprocess, "run", setup.mock_success_clone_repo)

    rv = scm.clone_private_repo(directory=setup.path)

    assert rv is True


def test_clone_private_repo_git_clone_fails(setup, monkeypatch, scm):
    monkeypatch.setattr(subprocess, "run", setup.mock_fail_return)

    with pytest.raises(SCMCloneRepoError) as e:
        scm.clone_private_repo(directory=setup.path)

    assert str(e.value) == "The repo could not be cloned"


def test_clone_private_repo_using_string_path(setup, monkeypatch, scm):
    monkeypatch.setattr(subprocess, "run", setup.mock_success_clone_repo)

    rv = scm.clone_private_repo(directory=str(setup.path))

    assert rv is True


def test_clone_private_repo_directory_already_exists(setup, monkeypatch, scm):
    monkeypatch.setattr(subprocess, "run", setup.mock_success_clone_repo)
    setup.make_repo_directory()

    rv = scm.clone_private_repo(directory=setup.path)

    assert rv is True


def test_clone_private_repo_directory_directory_missing(setup, monkeypatch, scm):
    monkeypatch.setattr(subprocess, "run", setup.mock_success_clone_repo)

    with pytest.raises(TypeError) as e:
        scm.clone_private_repo()

    assert str(e.value) == 'Must pass a value for the directory into this function'


def test_create_new_branch_in_repo_branch_missing(setup, scm):
    with pytest.raises(TypeError) as e:
        scm.create_new_branch_in_repo()

    assert str(e.value) == 'You must pass a branch name into this function'


def test_create_new_branch_in_repo_repo_not_setup(setup, scm):
    with pytest.raises(SCMCreateBranchError) as e:
        scm.repo_path = setup.path / setup.repo
        scm.create_new_branch_in_repo('fake_branch')

    assert str(e.value) == 'You must have a repo cloned before trying to create a branch'


def test_create_new_branch_in_repo_successfully(setup, monkeypatch, scm):
    monkeypatch.setattr(subprocess, "run", setup.mock_new_branch_success)
    setup.make_repo_directory()

    scm.repo_path = setup.path / setup.repo
    rv = scm.create_new_branch_in_repo(setup.branch)

    assert rv is True


def test_create_new_branch_in_repo_fails(setup, monkeypatch, scm):
    monkeypatch.setattr(subprocess, "run", setup.mock_fail_return)
    setup.make_repo_directory()

    scm.repo_path = setup.path / setup.repo

    with pytest.raises(SCMCreateBranchError) as e:
        scm.create_new_branch_in_repo('fake_branch')

    assert str(e.value) == "A new branch was not able to be created"


def test_write_data_to_file_in_repo_invalid_data_type(setup, scm):
    with pytest.raises(TypeError) as e:
        scm.write_data_to_file_in_repo("bad_data")

    assert str(e.value) == 'Must pass a dictionary to this function'


def test_write_data_to_file_in_repo_missing_repo_path(setup, scm):
    with pytest.raises(TypeError) as e:
        scm.write_data_to_file_in_repo(setup.valid_data)

    assert str(e.value) == "Must pass a string with the folder name of where the file will be stored into this function"


def test_write_data_to_file_in_repo(setup, scm):
    scm.repo_path = setup.make_repo_directory()

    rv = scm.write_data_to_file_in_repo(setup.valid_data, "test_file")

    assert rv is True
    assert scm.full_file_path.exists()


def test_write_data_to_file_in_repo_forgot_to_clone_repo_first(setup, scm):
    with pytest.raises(SCMWriteFileError) as e:
        scm.write_data_to_file_in_repo(setup.valid_data, "test_file")

    assert str(e.value) == "You must have a repo cloned before trying to create a file"


def test_write_data_to_file_in_repo_file_did_not_write(setup, monkeypatch, scm):
    monkeypatch.setattr(yaml, "dump", setup.remove_yaml_files)
    scm.repo_path = setup.make_repo_directory()

    with pytest.raises(SCMWriteFileError) as e:
        scm.write_data_to_file_in_repo(setup.valid_data, "test_file")

    assert str(e.value) == "Was not able to write the file to the filesystem"


def test_write_data_to_file_in_repo_with_custom_filename(setup, scm):
    scm.repo_path = setup.make_repo_directory()

    rv = scm.write_data_to_file_in_repo(setup.valid_data, "test_file")
    print(scm.full_file_path)
    assert rv is True
    assert scm.full_file_path.exists()
    assert "epgs" in str(scm.full_file_path)


def test_write_data_to_file_in_repo_invalid_directory(setup, scm):
    scm.repo_path = setup.make_repo_directory()

    with pytest.raises(SCMWriteFileError) as e:
        scm.write_data_to_file_in_repo(setup.valid_data, "nonexistant_directory")

    assert str(e.value) == "The path provided to save the file in does not exist"


def test_push_data_to_remote_repo(setup, monkeypatch, scm):
    monkeypatch.setattr(subprocess, "run", setup.mock_success_return)
    setup.make_repo_directory()

    scm.repo_path = setup.path
    rv = scm.push_data_to_remote_repo()

    assert rv is True


def test_push_data_to_remote_repo_repo_path_not_set(setup, scm):
    with pytest.raises(SCMPushDataError) as e:
        scm.push_data_to_remote_repo()

    assert str(e.value) == 'An undefined error occured while attempting to push the data'


def test_push_data_to_remote_repo_error_with_git_add(setup, monkeypatch, scm):
    monkeypatch.setattr(subprocess, "run", setup.mock_fail_with_push_during_add)
    setup.make_repo_directory()

    scm.repo_path = setup.path

    with pytest.raises(Exception) as e:
        scm.push_data_to_remote_repo()

    assert str(e.value) == "something bad happened while adding the file.  returncode: 128  stderr: b'it failed'"


def test_push_data_to_remote_repo_error_with_git_commit(setup, monkeypatch, scm):
    monkeypatch.setattr(subprocess, "run", setup.mock_fail_with_push_during_commit)
    setup.make_repo_directory()

    scm.repo_path = setup.path

    with pytest.raises(Exception) as e:
        scm.push_data_to_remote_repo()

    assert str(e.value) == "something bad happened while commiting the changes.  returncode: 128  stderr: b'it failed'"


def test_push_data_to_remote_repo_error_with_git_push(setup, monkeypatch, scm):
    monkeypatch.setattr(subprocess, "run", setup.mock_fail_with_push_during_push)
    setup.make_repo_directory()

    scm.repo_path = setup.path

    with pytest.raises(Exception) as e:
        scm.push_data_to_remote_repo()

    assert "something bad happened while pushing the branch.  returncode: 128  stderr: b'it failed'" in str(e.value)


def test_delete_local_copy_of_repo(setup, scm):
    repo = setup.make_repo_directory()
    assert repo.exists()

    scm.repo_path = setup.path

    scm.delete_local_copy_of_repo()

    assert not repo.exists()


def test_delete_local_copy_of_repo_an_error_occurs(setup, scm, monkeypatch):
    monkeypatch.setattr("shutil.rmtree", setup.raise_exception)
    repo = setup.make_repo_directory()
    assert repo.exists()

    scm.repo_path = setup.path

    with pytest.raises(SCMDeleteRepoError) as e:
        scm.delete_local_copy_of_repo()

    assert str(e.value) == "An error occured while attempting to delete the repo. <class 'Exception'> an exception from testing was raised"
