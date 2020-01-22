from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import yaml


class SCMCredentialValidationError(Exception):
    pass


class SCMCloneRepoError(Exception):
    pass


class SCMCreateBranchError(Exception):
    pass


class SCMWriteFileError(Exception):
    pass


class SCMPushDataError(Exception):
    pass


class SCMDeleteRepoError(Exception):
    pass


class SourceControlMgmt():
    def __init__(self, username=None, password=None, friendly_name=None, email=None, repo_name=None):
        self.username = username
        self.password = password
        self.friendly_name = friendly_name
        self.email = email
        self.repo_path = None
        self.repo_name = repo_name
        self.filename = None
        self.branch_name = None
        self.full_file_path = None
        self.relative_file_path = None

        exceptions = ['repo_path', 'filename', 'branch_name', 'full_file_path', 'relative_file_path']

        if not all(vars(self).values()):
            missing_values = [k for k, v in vars(self).items() if not v and k not in exceptions]
            if missing_values:
                raise TypeError(f"All values must have data.  The following attributes are empty: {missing_values}")

    def validate_scm_creds(self):
        """
        Verify user credentials will return the HEAD
        git ls-remote https://<user>:<password>@github.com/IGNW/pge-aci-epgs/ HEAD
        """
        results = subprocess.run(['git', 'ls-remote', f'https://{self.username}:{self.password}@github.com/IGNW/{self.repo_name}/', 'HEAD'],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 check=False)

        if results.returncode == 0 and b"HEAD" in results.stdout:
            return True

        raise SCMCredentialValidationError("The supplied credentials do not provide access to the given repo")

    def clone_private_repo(self, directory=None):
        """
        Clone the repo into the directory specified
        git clone https://<user>:<password>@github.com/IGNW/pge-aci-epgs /tmp/pge-aci-epgs
        """
        if directory is None:
            raise TypeError('Must pass a value for the directory into this function')

        # If the directory is a string, convert it to a PathLib object
        if isinstance(directory, str):
            d = Path(directory)
        elif isinstance(directory, Path):
            d = directory

        self.repo_path = d / self.repo_name

        if self.repo_path.exists() is True and self.repo_path.is_dir() is True:
            # Delete the directory
            print('Directory exists and is being deleted')
            shutil.rmtree(self.repo_path)

        results = subprocess.run(['git', 'clone', f'https://{self.username}:{self.password}@github.com/IGNW/{self.repo_name}/', f'{self.repo_path}'],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 check=False)
        # The git clone writes to stderr instead of stdout
        expected_string = f"Cloning into '{self.repo_path}'...\n"
        encoded_expected_string = expected_string.encode()

        if (results.returncode == 0 and
           encoded_expected_string == results.stderr and
           self.repo_path.exists() is True and
           self.repo_path.is_dir() is True):
            return True
        else:
            raise SCMCloneRepoError("The repo could not be cloned")

    def create_new_branch_in_repo(self, branch_name=None):
        """
        Create New Branch in existing repo
        cd /tmp/pge-aci-epgs
        git checkout -b NEW_TEST_BRANCH_NAME1
        """
        if not branch_name:
            raise TypeError('You must pass a branch name into this function')
        else:
            self.branch_name = branch_name

        if self.repo_path and self.repo_path.exists() is True and self.repo_path.is_dir() is True:
            results = subprocess.run(["git", "checkout", "-b", branch_name], cwd=self.repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        else:
            raise SCMCreateBranchError('You must have a repo cloned before trying to create a branch')

        expected_results = f"Switched to a new branch '{self.branch_name}'\n"

        if results.returncode == 0 and expected_results.encode() == results.stderr:
            return True
        else:
            raise SCMCreateBranchError("A new branch was not able to be created")

    def write_data_to_file_in_repo(self, data, file_path=None):
        """
        Write the yaml data to a file in the repo
        """
        if not isinstance(data, dict):
            raise TypeError('Must pass a dictionary to this function')

        if file_path is None:
            raise TypeError('Must pass a string with the folder name of where the file will be stored into this function')

        # if 'schema' not in data.keys() and 'epgname' not in data.keys():
        #    raise ValueError('Must be a properly formatted aci dictionary object to use this function')

        now = datetime.now()
        str_now = now.strftime("%Y%m%d-%H%M%S")

        self.filename = f"{file_path}-{str_now}.yaml"

        if self.repo_path and self.repo_path.exists() is True and self.repo_path.is_dir() is True:
            self.full_dir_path = self.repo_path / f"{file_path}"
            self.full_file_path = self.full_dir_path / self.filename
            self.relative_file_path = f'{file_path}/{self.filename}'

            if self.full_file_path.exists():
                raise SCMWriteFileError('This file already exists in the repo')
            elif not self.full_dir_path.exists():
                raise SCMWriteFileError('The path provided to save the file in does not exist')
            else:
                with open(self.full_file_path, 'w') as outfile:
                    yaml.dump(data, outfile, explicit_start=True, explicit_end=True, default_flow_style=False)
        else:
            raise SCMWriteFileError('You must have a repo cloned before trying to create a file')

        if self.full_file_path.exists():
            return True
        else:
            raise SCMWriteFileError('Was not able to write the file to the filesystem')

    def push_data_to_remote_repo(self):
        """
        Commit the changes and push the branch to master
        """

        if self.repo_path and self.repo_path.exists() is True and self.repo_path.is_dir() is True:
            results = subprocess.run(["git", "add", f"{self.relative_file_path}"],
                                     cwd=self.repo_path, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, check=False)

            if results.returncode != 0:
                raise SCMPushDataError(f"something bad happened while adding the file.  returncode: {results.returncode}  stderr: {results.stderr}")

            command = ["git", "-c", f"user.name='{self.username}'", "-c", f"user.email='{self.email}'", "commit", "-m", "Adding file to repo from python"]
            results = subprocess.run(command, cwd=self.repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

            if results.returncode != 0:
                raise SCMPushDataError(f"something bad happened while commiting the changes.  returncode: {results.returncode}  stderr: {results.stderr}")

            dest = f'https://{self.username}:{self.password}@github.com/IGNW/{self.repo_name}/'
            src = f'{self.branch_name}'

            results = subprocess.run(['git', 'push', dest, src], cwd=self.repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

            if results.returncode != 0:
                print('dest:', dest)
                print('src:', src)
                raise SCMPushDataError(f"something bad happened while pushing the branch.  "
                                       f"returncode: {results.returncode}  stderr: {results.stderr} "
                                       f"repo: {self.repo_name} branch: {self.branch_name}")
            else:
                return True

        else:
            raise SCMPushDataError("An undefined error occured while attempting to push the data")

    def delete_local_copy_of_repo(self):
        """
        Delete the local repo when action is completed
        """
        try:
            shutil.rmtree(self.repo_path)
            return True
        except Exception as e:
            raise SCMDeleteRepoError(f"An error occured while attempting to delete the repo. {type(e)} {e}")
