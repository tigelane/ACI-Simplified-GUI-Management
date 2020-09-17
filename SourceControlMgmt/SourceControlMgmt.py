from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import yaml
import requests


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


class SCMGraphQLError(Exception):
    pass


class SourceControlMgmt():
    def __init__(self, username=None, password=None, friendly_name=None, email=None, repo_name=None, repo_owner=None):
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
        self.existing_branches = {}
        self.git_hub_graphql_api = 'https://api.github.com/graphql'
        self.github_repo_id = None
        self.repo_owner = self.username if not repo_owner else repo_owner

        self.get_github_repo_id()

        exceptions = ['repo_path', 'filename', 'branch_name', 'full_file_path', 'relative_file_path', 'existing_branches']

        if not all(vars(self).values()):
            missing_values = [k for k, v in vars(self).items() if not v and k not in exceptions]
            if missing_values:
                raise TypeError(f"All values must have data.  The following attributes are empty: {missing_values}")

    def validate_scm_creds(self):
        """
        Verify user credentials will return the HEAD
        git ls-remote https://<user>:<password>@github.com/IGNW/pge-aci-epgs/ HEAD
        """
        results = subprocess.run(['git', 'ls-remote', f'https://{self.username}:{self.password}@github.com/{self.repo_owner}/{self.repo_name}/', 'HEAD'],
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

        results = subprocess.run(['git', 'clone', f'https://{self.username}:{self.password}@github.com/{self.repo_owner}/{self.repo_name}/', f'{self.repo_path}'],
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

    def write_data_to_file_in_repo(self, data, file_path=None, file_name=None, append_timestamp=False, as_yaml=False):
        """
        Write the data to a file in the repo
        """

        if file_path is None:
            raise TypeError('Must pass a string with the folder name of where the file will be stored into this function')

        if as_yaml and not isinstance(data, dict):
            raise TypeError('Must pass a dictionary to this function')

        # if 'schema' not in data.keys() and 'epgname' not in data.keys():
        #    raise ValueError('Must be a properly formatted aci dictionary object to use this function')

        now = datetime.now()
        str_now = now.strftime("%Y%m%d-%H%M%S")

        if append_timestamp:
            file_parts = file_name.split('.')
            if len(file_parts) > 1:
                self.filename = f"{file_parts[0]}-{str_now}.{file_parts[1]}"
            else:
                self.filename = f"{file_name}-{str_now}"
        else:
            self.filename = f"{file_name}"

        if self.repo_path and self.repo_path.exists() is True and self.repo_path.is_dir() is True:
            self.full_dir_path = self.repo_path / f"{file_path}"
            self.full_file_path = self.full_dir_path / self.filename
            self.relative_file_path = f'{file_path}/{self.filename}' if file_path else f'{self.filename}'

            if self.full_file_path.exists():
                raise SCMWriteFileError(f'This file already exists in the repo: {self.full_file_path}')
            elif not self.full_dir_path.exists():
                raise SCMWriteFileError('The path provided to save the file in does not exist')
            else:
                if as_yaml:
                    with open(self.full_file_path, 'w') as outfile:
                        yaml.dump(data, outfile, explicit_start=True, explicit_end=True, default_flow_style=False)
                else:
                    with open(self.full_file_path, 'w') as outfile:
                        outfile.write(data)
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

            dest = f'https://{self.username}:{self.password}@github.com/{self.repo_owner}/{self.repo_name}/'
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

    def _gql_query(self, query=None, vars=None):
        """
        Helper function to call the GraphQL enpoint in GitHub
        """
        if query is None:
            raise TypeError("A GraphQL query is required to run this function")

        headers = {"Authorization": f"token {self.password}"}
        request = requests.post(self.git_hub_graphql_api, json={'query': query, 'variables': vars}, headers=headers)

        try:
            data = request.json()
            if data['data'].get("errors"):
                error = data['data']['errors']
                raise SCMGraphQLError(f"An error in GraphQL occured.  See the following for more info: {error}")
            else:
                return data

        except Exception as e:
            print(e)
            print(type(e))
            print(dir(e))
            print(request)
            raise

    def get_github_repo_id(self):
        """
        Takes the github user id and repo name and gets the github internal id
        """

        query = """
        query RepoIDQuery($repo_name: String!, $owner: String!) {
            repository(name: $repo_name, owner: $owner) {
                id
            }
        }
        """

        variables = {
            "repo_name": self.repo_name,
            "owner": self.repo_owner
        }
        print (variables)

        response = self._gql_query(query=query, vars=variables)
        print (response)
        self.github_repo_id = response['data']['repository']['id']

    def create_git_hub_pull_request(self, destination_branch=None, source_branch=None, title=None, body=None):
        """
        Create a Pull Request in GitHub

        Takes 2 branch names, title, body, and the repo ID
        """

        if destination_branch is None or source_branch is None:
            raise TypeError("Must have a source and destination branch to create a Pull Request")

        mutation = """
            mutation MyMutation($repo_id: String!, $dest_branch: String!, $src_branch: String!, $title: String!, $body: String!) {
                __typename
                createPullRequest(input: {repositoryId: $repo_id,
                                          baseRefName: $dest_branch,
                                          headRefName: $src_branch,
                                          title: $title,
                                          body: $body}) {
                    pullRequest {
                        number,
                        url
                    }
                }
            }
        """

        variables = {
            "repo_id": self.github_repo_id,
            "dest_branch": destination_branch,
            "src_branch": source_branch,
            "title": title,
            "body": body
        }

        data = self._gql_query(query=mutation, vars=variables)

        return data

    def get_all_current_branches(self):
        """
        Pull the last 10 branches and ref ID's from a github repo
        """

        query = """
        query BranchQuery($repo_name: String!, $owner: String!) {
            repository(name: $repo_name, owner: $owner) {
                name
                nameWithOwner
                refs(refPrefix: "refs/heads/", last: 10) {
                    totalCount
                    nodes {
                        id
                        name
                    }
                }
            }
        }
        """

        variables = {
            "owner": self.repo_owner,
            "repo_name": self.repo_name
        }

        data = self._gql_query(query=query, vars=variables)

        for ref in data['data']['repository']['refs']['nodes']:
            id = ref['id']
            name = ref['name']
            self.existing_branches[name] = id
