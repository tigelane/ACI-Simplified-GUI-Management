import pytest
from unittest.mock import patch
import gag
from flask import request, session
from requests.exceptions import ConnectionError
from SourceControlMgmt.SourceControlMgmt import SCMDeleteRepoError


@pytest.fixture
def client():
    gag.app.config['TESTING'] = True
    gag.app.config['SECRET_KEY'] = 'fakekey'
    gag.app_context = gag.app.test_request_context()
    gag.app_context.push()
    client = gag.app.test_client()

    yield client


@pytest.fixture
def app():
    with gag.app.app_context() as app:
        yield app


@pytest.fixture
def MockSCM():
    class MockedSCM():
        def __init__(*args, **kwargs):
            pass

        def validate_scm_creds(self):
            pass

        def clone_private_repo(self, directory=None):
            pass

        def create_new_branch_in_repo(self, branch_name=None):
            pass

        def write_data_to_file_in_repo(self, data=None, file_path=None):
            pass

        def push_data_to_remote_repo(self):
            pass

        def delete_local_copy_of_repo(self):
            pass
    return MockedSCM


def test_test_for_login_info_no_login_info(client):
    with client as c:
        with c.session_transaction():
            pass    # For this test just need a fake session

        c.get('/')  # Setting up a fake session to test the function

        rv = gag.test_for_login_info()
        assert rv is False


def test_test_for_login_info_all_login_info(client):
    with client as c:
        with c.session_transaction() as session:
            session['apic'] = 'fake_apic'
            session['username'] = 'fake_username'
            session['password'] = 'fake_password'

        c.get('/')   # Setting up a fake session to test the function

        rv = gag.test_for_login_info()
        assert rv is True


def test_test_for_login_info_no_user_name(client):
    with client as c:
        with c.session_transaction() as session:
            session['username'] = 'fake_username'
            session['password'] = 'fake_password'

        c.get('/')   # Setting up a fake session to test the function

        rv = gag.test_for_login_info()
        assert rv is False


def test_test_for_login_info_no_password_name(client):
    with client as c:
        with c.session_transaction() as session:
            session['apic'] = 'fake_apic'
            session['password'] = 'fake_password'

        c.get('/')   # Setting up a fake session to test the function

        rv = gag.test_for_login_info()
        assert rv is False


def test_clean_string_matching_data():
    rv = gag.clean_string('(test_data)')
    assert isinstance(rv, str)
    assert rv == 'test_data'


def test_clean_string_no_matching_data():
    rv = gag.clean_string('non_matching_test_data')
    assert isinstance(rv, str)
    assert rv == ''


def test_clean_string_int_search_data():
    rv = gag.clean_string(42)
    assert isinstance(rv, str)
    assert rv == ''


def test_clean_data_matching_data_with_valid_data(client):
    test_data = {
        "my_test": "(test_data)",
        "expected_results": "test_data"
    }
    with client as c:
        c.get('/', data=test_data)
        rv = gag.clean_data(request, 'my_test')

        assert isinstance(rv, str)
        assert rv == test_data['expected_results']


def test_clean_data_matching_data_with_invalid_data(client):
    test_data = {
        "my_test": "bad_test_data",
        "expected_results": ""
    }
    with client as c:
        c.get('/', data=test_data)
        rv = gag.clean_data(request, 'my_test')

        assert isinstance(rv, str)
        assert rv == test_data['expected_results']


def test_document_header(client):
    expected_results = '''<!DOCTYPE html> 
<!-- Takes  title, style_1, style_2 and the theme letter  (the latter three from http://themeroller.jquerymobile.com) -->
<html> 
    <head> 
    <title>ACI Workflows</title> 
    <meta name="viewport" content="width=device-width, initial-scale=1"> 

    <!-- Custom CSS for application -->
    <link rel="stylesheet" href="/static/themes/dlt_themes.min.css"/>
    <link rel="stylesheet" href="/static/themes/jquery.mobile.icons.min.css"/>

    <link rel="stylesheet" href="/static/jquery.mobile.structure-1.4.5.min.css" />
    <script src="/static/jquery-1.11.1.min.js"></script>
    <script src="/static/jquery.mobile-1.4.5.min.js"></script>
</head>


<!-- End document_header.html -->'''  # NOQA - some line causes flake8 issues

    with client:
        rv = gag.document_header()
        assert rv == expected_results


def test_document_footer(client):
    expected_results = '''    <!-- Begin document_footer.html -->
    </div><!-- /page -->
</body>
</html>'''

    with client:
        rv = gag.document_footer()
        assert rv == expected_results


def test_render_error_with_string(client):
    error_message = "Test Error from Pytest"
    expected_results = '<H2 color="red">Test Error from Pytest</H2>'
    with client:
        rv = gag.render_error_screen(error_message)
        assert expected_results in rv


def test_basic_render_with_index_html(client):
    rendering_file = 'index.html'
    page_header = "PyTest Testing"
    data_url = ""
    form_data = []

    expected_header = f"<h1>{page_header}</h1>"

    with client:
        rv = gag.basic_render(data_url, page_header, rendering_file, form_data)
        assert expected_header in rv


def test_slash_route(client):
    with client as c:
        rv = c.get('/')
        assert rv.content_type == "text/html; charset=utf-8"
        assert b"<title>ACI Workflows</title>" in rv.data
        assert rv.is_json is False
        assert rv.status_code == 200


def test_slash_index_route(client):
    with client as c:
        rv = c.get('/index')
        assert rv.content_type == "text/html; charset=utf-8"
        assert b"<title>ACI Workflows</title>" in rv.data
        assert rv.is_json is False
        assert rv.status_code == 200


def test_login_get_route_with_apic_data(client):
    with client as c:
        with c.session_transaction() as session:
            session['apic'] = 'fake_apic'
            session['username'] = 'fake_username'
            session['password'] = 'fake_password'

        rv = c.get('/login')
        assert rv.status_code == 303
        assert rv.location == 'http://localhost/server_info'


def test_login_get_route_without_apic_data(client):
    with client as c:
        with c.session_transaction():
            pass
        rv = c.get('/login')
        assert rv.status_code == 200
        assert b"Sign in" in rv.data


@patch("gag.aci")
def test_login_post_route_login_ok(mock_aci, client):
    test_data = {
        "apic": "256.2.3.4",
        "username": "fake_user",
        "password": "fake_pw"
    }

    class MockACI():
        def login(self):
            return MockACILogin()

    class MockACILogin():
        def __init__(self):
            self.ok = True

    mock_aci.Session.return_value = MockACI()

    with client as c:
        rv = c.post('/login', data=test_data)
        assert rv.status_code == 303
        assert rv.location == 'http://localhost/server_info'
        assert rv.content_type == 'text/html; charset=utf-8'


@patch("gag.aci")
def test_login_post_route_login_not_ok(mock_aci, client):
    test_data = {
        "apic": "256.2.3.4",
        "username": "fake_user",
        "password": "fake_pw"
    }

    class MockACI():
        def login(self):
            return MockACILogin()

    class MockACILogin():
        def __init__(self):
            self.ok = False

    mock_aci.Session.return_value = MockACI()

    with client as c:
        rv = c.post('/login', data=test_data)
        assert rv.status_code == 302
        assert rv.location == 'http://localhost/login'
        assert rv.content_type == 'text/html; charset=utf-8'


def test_get_fabric_friendly_name_no_fabric_names_defined(client):
    test_url = 'http://www.fake.com'

    with client:
        rv = gag.get_fabric_friendly_name(test_url)
        assert rv == test_url


def test_get_fabric_friendly_name_fabric_names_defined(client):
    test_url = 'http://www.fake.com'

    gag.app.settings.fabric_names = {
        'http://www.fake.com': "Fake Fabric Name"
    }

    with client:
        rv = gag.get_fabric_friendly_name(test_url)
        assert rv == gag.app.settings.fabric_names[test_url]


def test_base_menu_no_creds(client):
    gag.creds = {}
    with client:
        rv = gag.base_menu()

        assert "System Login" in rv
        assert isinstance(rv, str)


def test_base_menu_with_creds(client):
    gag.creds = {"apic": "256.2.3.4"}

    with client:
        rv = gag.base_menu()

        assert "System Login" in rv
        assert isinstance(rv, str)


def test_add_epg(client):
    with client as c:
        rv = c.get('/addepg')

        assert rv.status_code == 200
        assert b"New EPG Name" in rv.data
        assert rv.content_type == 'text/html; charset=utf-8'


def test_save_addepg_get_method(client):
    with client as c:
        rv = c.get('/save_addepg')

        assert rv.status_code == 303
        assert rv.location == "http://localhost/"


def test_save_addepg_post_method_with_close_in_form(client):
    test_data = {"close": True}

    with client as c:
        rv = c.post('/save_addepg', data=test_data)

        assert rv.status_code == 303
        assert rv.location == "http://localhost/"


def test_save_addepg_post_method_with_missing_data(app, client):
    expected_return = ('\n<div style="text-align:center;">\n    '
                       '<h1 style="color:red">Failure!!</h1>\n    '
                       'The config changes did not get pushed to source control.\n\n    '
                       '<h2>Additional Information</h2> \n    '
                       'Not all form data was passed to the save page\n</div>\n')

    test_data = {}

    with client as c:
        rv = c.post('/save_addepg', data=test_data)

        assert rv.status_code == 303
        assert rv.location == 'http://localhost/index'
        assert session['message'] == expected_return


def test_save_addepg_post_method_with_data(app, client, monkeypatch):
    def mockreturn(*args, **kwargs):
        session['message'] = "a message"

    monkeypatch.setattr("gag.write_data_to_git_repo", mockreturn)

    test_data = {
        'datacenter': '(fake_dc)',
        'tenant': '(fake_tenant)',
        'apppro': '(fake_appro)',
        'epgname': '(fake_epgname)',
        'description': '(description)',
        'legacy_vlan': '(legacy_vlan)',
        'SCM Username': "fake_user",
        'SCM Password': "fake_pw",
        'SCM Name': "fake_name",
        'SCM Email': "fake_email"
        }

    with client as c:
        rv = c.post('/save_addepg', data=test_data)

        assert rv.status_code == 303
        assert rv.location == "http://localhost/index"
        assert session.get('message', '') == "a message"


def test_save_addepg_post_method_with_missing_data_for_testing_if_statements(app, client, monkeypatch):
    expected_return = ('\n<div style="text-align:center;">\n    '
                       '<h1 style="color:red">Failure!!</h1>\n    '
                       'The config changes did not get pushed to source control.\n\n    '
                       '<h2>Additional Information</h2> \n    '
                       'Not all form data was passed to the save page\n</div>\n')

    test_data = {}

    with client as c:
        rv = c.post('/save_addepg', data=test_data)

        assert rv.status_code == 303
        assert rv.location == "http://localhost/index"
        assert session.get('message', '') == expected_return


def test_save_addepg_post_method_with_data_for_testing_if_statements(app, client, monkeypatch):
    def mockreturn(*args, **kwargs):
        session['message'] = "a message"

    monkeypatch.setattr("gag.write_data_to_git_repo", mockreturn)

    test_data = {
        'datacenter': '(fake_dc)',
        'tenant': '(fake_tenant)',
        'apppro': '(fake_appro)',
        'epgname': '(fake_epgname)',
        'description': '(description)',
        'legacy_vlan': '(legacy_vlan)',
        'bridge_domain': 'fake_bd',
        'default_gateway': 'fake_dg',
        'netapp_storage': 'fake_nas',
        'RCC_ACI': 'fake',
        'RCC_VXBLOCK_ACI': 'fake',
        'WTC_ACI': 'fake',
        'WTC_VXBLOCK_ACI': 'fake',
        'SCM Username': "fake_user",
        'SCM Password': "fake_pw",
        'SCM Name': "fake_name",
        'SCM Email': "fake_email"
        }

    with client as c:
        rv = c.post('/save_addepg', data=test_data)

        assert rv.status_code == 303
        assert rv.location == "http://localhost/index"
        assert session.get('message') == "a message"


def test_add_ucs(client):
    with client as c:
        rv = c.get('/adducs')

        assert rv.status_code == 200
        assert b'Add a UCS Cluster' in rv.data
        assert rv.content_type == 'text/html; charset=utf-8'


def test_save_adducs_get_method(client):
    with client as c:
        rv = c.get('/save_adducs')

        assert rv.status_code == 303
        assert rv.location == "http://localhost/"


def test_save_adducs_post_method_with_close_in_form(client):
    test_data = {"close": True}

    with client as c:
        rv = c.post('/save_adducs', data=test_data)

        assert rv.status_code == 303
        assert rv.location == "http://localhost/"


def test_save_adducs_post_method_with_data_vpc_in_form(client):
    test_data = {
        'datacenter': 'fake_dc',
        'newname': 'fake_new_name',
        'description': 'fake_desc',
        'leafpair': 'fake_leafpair',
        'port': 'fake_port',
        'vpc': 'fake_vpc'
        }

    with client as c:
        rv = c.post('/save_adducs', data=test_data)

        assert rv.status_code == 303
        assert rv.location == "http://localhost/index"


def test_save_adducs_post_method_with_data_vpc_not_in_form(client):
    test_data = {
        'datacenter': 'fake_dc',
        'newname': 'fake_new_name',
        'description': 'fake_desc',
        'leafpair': 'fake_leafpair',
        'port': 'fake_port'
        }

    with client as c:
        rv = c.post('/save_adducs', data=test_data)

        assert rv.status_code == 303
        assert rv.location == "http://localhost/index"


def test_add_vxrail(client):
    with client as c:
        rv = c.get('/addvxrail')

        assert rv.status_code == 200
        assert b'Add a VXRail Cluster' in rv.data
        assert rv.content_type == 'text/html; charset=utf-8'


def test_save_addvxrail_get_method(client):
    with client as c:
        rv = c.get('/save_addvxrail')

        assert rv.status_code == 303
        assert rv.location == "http://localhost/"


def test_save_addvxrail_post_method_with_close_in_form(client):
    test_data = {"close": True}

    with client as c:
        rv = c.post('/save_addvxrail', data=test_data)

        assert rv.status_code == 303
        assert rv.location == "http://localhost/"


def test_save_addvxrail_post_method_with_missing_data_in_form(app, client):
    expected_return = ('\n<div style="text-align:center;">\n    '
                       '<h1 style="color:red">Failure!!</h1>\n    '
                       'The config changes did not get pushed to source control.\n\n    '
                       '<h2>Additional Information</h2> \n    '
                       'Not all form data was passed to the save page\n</div>\n')

    test_data = {}

    with client as c:
        rv = c.post('/save_addvxrail', data=test_data)

        assert rv.status_code == 303
        assert rv.location == "http://localhost/index"
        assert session.get('message', '') == expected_return


def test_save_addvxrail_post_method_with_data_in_form(app, client, monkeypatch):
    def mockreturn(*args, **kwargs):
        session['message'] = "a message"
    monkeypatch.setattr("gag.write_data_to_git_repo", mockreturn)

    test_data = {
        'vxrail_int_selector_appendix': 'fake_vxrail_int_selector_appendix',
        'vxrail_policy_group': 'fake_vxrail_policy_group',
        'datacenter': 'fake_datacenter',
        'newname': 'fake_newname',
        'description': 'fake_description',
        'leafpair': 'fake_leafpair',
        'port': 'fake_port',
        'SCM Username': "fake_user",
        'SCM Password': "fake_pw",
        'SCM Name': "fake_name",
        'SCM Email': "fake_email"
        }

    with client as c:
        rv = c.post('/save_addvxrail', data=test_data)

        assert rv.status_code == 303
        assert rv.location == "http://localhost/index"
        assert session.get('message', '') == "a message"


def test_render_login_screen(client):
    with client:
        rv = gag.render_login_screen()
        print(rv)
        print(dir(rv))
        assert rv.status_code == 303
        assert rv.location == "/login"


@patch('gag.requests')
def test_get_url_fake_good_url_fail_to_load_data_from_server(mock_request, client):
    test_url = 'http://www.fake.com'
    fake_json = '{"general": {"status": "FAIL", "results": "Fake Results"}}'

    class fake_requests_response():
        def __init__(self):
            self.text = fake_json
            self.status_code = 200

    mock_request.get.return_value = fake_requests_response()

    with client:
        rv = gag.get_url(test_url)
        assert rv['result'] == 0
        assert "Database Failure" in rv['data']


@patch('gag.requests')
def test_get_url_fake_good_url_results_is_empty(mock_request, client):
    test_url = 'http://www.fake.com'
    fake_json = '{"general": {"status": "0", "results": []}}'

    class fake_requests_response():
        def __init__(self):
            self.text = fake_json
            self.status_code = 200

    mock_request.get.return_value = fake_requests_response()

    with client:
        rv = gag.get_url(test_url)
        assert rv['result'] == 0
        assert "No records found" in rv['data']


@patch('gag.requests')
def test_get_url_fake_good_url_results_contains_data(mock_request, client):
    test_url = 'http://www.fake.com'
    fake_json = '{"general": {"status": "0", "results": ["thing1", "thing2"]}}'

    class fake_requests_response():
        def __init__(self):
            self.text = fake_json
            self.status_code = 200

    mock_request.get.return_value = fake_requests_response()

    with client:
        rv = gag.get_url(test_url)
        assert rv['result'] == 1
        assert len(rv['data']['general']['results']) == 2
        assert "thing1" in rv['data']['general']['results']


@patch('gag.requests')
def test_get_url_with_202_status_code(mock_request, client):
    test_url = 'http://www.fake.com'
    fake_json = '{"general": {"status": "0", "results": ["thing1", "thing2"]}}'

    class fake_requests_response():
        def __init__(self):
            self.text = fake_json
            self.status_code = 202

    mock_request.get.return_value = fake_requests_response()

    with client:
        rv = gag.get_url(test_url)
        assert rv['result'] == 0
        assert "Non 200 HTML response" in rv['data']


@patch('gag.requests')
def test_get_url_fake_bad_url_results_contains_data(mock_request, client):
    test_url = 'http://www.fake.local'

    mock_request.get.side_effect = ConnectionError

    with client:
        rv = gag.get_url(test_url)
        assert rv['result'] == 0
        assert "Application Server Failure" in rv['data']


def test_table_header(client):
    with client:
        rv = gag.table_header()

        assert isinstance(rv, str)
        assert "<head>" in rv


def test_table_footer(client):
    with client:
        rv = gag.table_footer()

        assert isinstance(rv, str)
        assert "</html>" in rv


def test_source_control_credential_input(client):
    rv = gag.source_control_credential_input()
    assert isinstance(rv, str)
    assert "SCM" in rv


def test_write_data_to_git_repo_no_data(client):
    with client:
        with pytest.raises(TypeError) as e:
            gag.write_data_to_git_repo()
            assert str(e.values) == ("All values must have data.  "
                                     "The following attributes are empty: "
                                     "['username', 'password', 'friendly_name', 'email']")


def test_write_data_to_git_repo(app, client, monkeypatch, MockSCM):
    monkeypatch.setattr("gag.SourceControlMgmt.SourceControlMgmt", MockSCM)
    with client:
        gag.write_data_to_git_repo()
        assert "Data successfully pushed to Source Control" in session.get('message', '')


def test_write_data_to_git_repo_an_error_occurs(app, client, monkeypatch, MockSCM):
    expected_return = ('\n<div style="text-align:center;">\n    '
                       '<h1 style="color:red">Failure!!</h1>\n    '
                       'The config changes did not get pushed to source control.\n\n    '
                       '<h2>Additional Information</h2> \n    '
                       'The file was not pushed to Source Control.  '
                       'Error: &#39;A mock TypeError occured&#39;\n</div>\n')

    class m_scm(MockSCM):
        def delete_local_copy_of_repo(self):
            raise TypeError("A mock TypeError occured")

    monkeypatch.setattr("gag.SourceControlMgmt.SourceControlMgmt", m_scm)
    with client:
        gag.write_data_to_git_repo()
        assert session.get('message', '') == expected_return


def test_write_data_to_git_repo_a_delete_error_occurs(app, client, monkeypatch, MockSCM):
    expected_return = ('\n<div style="text-align:center;">\n    '
                       '<h1 style="color:red">Failure!!</h1>\n    '
                       'The config changes did not get pushed to source control.\n\n    '
                       '<h2>Additional Information</h2> \n    '
                       'The repo was not deleted.  '
                       'Error: &#39;A mock delete error occured&#39;\n</div>\n')

    class m_scm(MockSCM):
        def delete_local_copy_of_repo(self):
            raise SCMDeleteRepoError("A mock delete error occured")

    monkeypatch.setattr("gag.SourceControlMgmt.SourceControlMgmt", m_scm)
    with client:
        gag.write_data_to_git_repo()
        assert session.get('message', '') == expected_return


def test_index_page_message_default_values():
    expected_return = ('\n<div style="text-align:center;">\n    '
                       '<h1 style="color:orange">Error!!</h1>\n    '
                       'An error occured, see below for any additional '
                       'information that may be available\n\n    '
                       '<h2>Additional Information</h2> \n    \n</div>\n')

    rv = gag.index_page_message()
    assert rv == expected_return


def test_index_page_message_unknown_success_message():
    expected_return = ('\n<div style="text-align:center;">\n    '
                       '<h1 style="color:orange">Error!!</h1>\n    '
                       'An error occured, see below for any additional '
                       'information that may be available\n\n    '
                       '<h2>Additional Information</h2> \n    \n</div>\n')

    rv = gag.index_page_message(success="invalid")
    assert rv == expected_return


def test_index_page_message_success():
    success_message = "This is a success message!!!5577"
    url = "https://test_url.local"

    expected_return = ('\n\n<div style="text-align:center;">\n    '
                       '<h1 style="color:green">SUCCESS!!</h1>\n    '
                       'Navigate to the folling URL to review the config file '
                       'and raise a Pull Request<br>\n    '
                       f'<a href="{url}" target="_blank">{url}</a>\n\n    '
                       '<h2>Additional Information</h2> \n    '
                       f'{success_message}\n</div>\n')

    rv = gag.index_page_message(msg=success_message, success=True, url=url)
    assert success_message in rv
    assert url in rv
    assert rv == expected_return


def test_index_page_message_fail():
    fail_message = "This is a failure message 4455!!"

    expected_return = ('\n<div style="text-align:center;">\n    '
                       '<h1 style="color:red">Failure!!</h1>\n    '
                       'The config changes did not get pushed to source control.\n\n    '
                       '<h2>Additional Information</h2> \n    '
                       f'{fail_message}\n</div>\n')

    rv = gag.index_page_message(success=False, msg=fail_message)

    assert fail_message in rv
    assert rv == expected_return
