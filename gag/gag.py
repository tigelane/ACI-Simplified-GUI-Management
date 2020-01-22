#!/usr/bin/env python3

# Import Standard Library Packages
from datetime import datetime
from requests.exceptions import ConnectionError
from SourceControlMgmt import SourceControlMgmt
from SourceControlMgmt.SourceControlMgmt import SCMDeleteRepoError
from Settings.Settings import Settings
from werkzeug.exceptions import BadRequestKeyError
import sys
import requests
import re
import random
import json
import time
import inspect
import secrets

# Import common community packages
from flask import Flask, request, render_template, url_for, redirect, session, Markup

# Import Cisco Libraries
from acitoolkit import Node, ExternalSwitch, Endpoint
import acitoolkit.acitoolkit as aci

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'memcached'
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)
app.settings = Settings()


def clean_data(request, input):
    my_search = re.search(r'\((.*)\)', str(request.form[input]))

    if my_search is not None:
        return my_search.group(1)
    else:
        return ''


def clean_string(input):
    my_search = re.search(r'\((.*)\)', str(input))

    if my_search is not None:
        return my_search.group(1)
    else:
        return ''


# TODO - Get write_log Working, not being called currently
def write_log(entry):
    if app.settings.log_file_enable == False:
        return

    try:
        log_file = open(app.settings.log_file_name, "a")
    except:
        print("BAD  - Unable to open file for append:   {0}\n".format(app.settings.log_file_name))
        sys.exit()

    logEntry = "{0} - Calling Function: {1}".format(entry, inspect.stack()[1][3])
    log_file.write(logEntry)
    log_file.close()
    print("Log Entry: {}".format(logEntry))


# TODO - Most of the if statement is not used since 'data_url' is never updated
def basic_render(data_url, page_header, rendering_file, form_data):
    if data_url != "":
        data = get_url(data_url)
        if data['result'] == 0:
            return data['data']
        else:
            app.settings.records = data['data']['general']['results']
    else:
        app.settings.records = []

    html = document_header()
    html += render_template(rendering_file, url_base=app.settings.url_base,
                            page_header=page_header, theme=app.settings.theme, theme_cancel=app.settings.theme_cancel,
                            records=app.settings.records, form_data=form_data, message=session.get('message', ''))
    html += document_footer()

    session['message'] = ''
    return html


@app.route('/')
def default():

    rendering_file = 'index.html'
    page_header = "ACI Workflows"
    return basic_render(app.settings.data_url, page_header, rendering_file, app.settings.form_data)


@app.route('/index')
def index():
    return default()


def login_to_apic():
    """
    Use local credentials file to login to APIC.
    :return: session object used by acitools.
    """
    # Verify if there is a credentials file and return an error if there isn't one
    # try:
    #     credsfile = open(credsfilename, "r")
    # except:
    #     error = 'No credentials file found: {0}'.format(credsfilename)
    #     error_screen = render_error_screen(error)
    #     return ['error', error, error_screen]

    # Uses credentials in the local directory to login
    # Returns either the session object or a list if there is an error
    # Check for a return type of list if there is an error
    # value 0 = 'error', value 1 = error text, value 2 = full html page
    # description = ('WICAT')
    # creds = aci.Credentials('apic', description)
    # args = creds.get()
    # session = aci.Session(args.url, args.login, args.password)
    creds = app.settings.apic_creds

    try:
        session = aci.Session(creds['url'], creds['username'], creds['password'])
    except:
        error = 'No credentials found'
        error_screen = render_login_screen()
        return ['error', error, error_screen]

    resp = session.login()
    if not resp.ok:
        error = 'Could not login to APIC.'
        error_screen = render_error_screen(error)
        return ['error', error, error_screen]

    return session


def render_login_screen():
    return redirect('/login', code=303)


@app.route('/login', methods=['GET'])
def login_get():
    # check for login data in session and redirect if exists
    if test_for_login_info():
        return redirect("/server_info", code=303)
    try:    # TODO - need to verify request.args will get called
        apic = request.args.get('apic_ip')[8:]
    except TypeError:
        apic = ''

    html = base_menu()
    html += render_template('login.html', apic=apic)

    return html


@app.route('/login', methods=['POST'])
def login_post():
    # TODO: test creds against apic

    s = aci.Session('https://%s' % (request.form['apic']),
                    request.form['username'],
                    request.form['password'])

    try:
        assert (s.login().ok)  # TODO - don't do this, assert can be disabled to always not fail
    except:
        # return redirect('login?usr=%s&apic=%s' % (request.form['username'], request.form['apic']))
        return redirect('/login')

    app.settings.apic_creds['url'] = 'https://%s' % (request.form['apic'])
    app.settings.apic_creds['username'] = str(request.form['username'])
    app.settings.apic_creds['password'] = str(request.form['password'])
    return redirect('/server_info', code=303)


def test_for_login_info():
    try:
        var = session['apic']
        var = session['username']
        var = session['password']
        return True
    except:
        return False


# TODO - Need to test
@app.route('/enter_creds')
def enter_creds():
    """
    Authenticate user against APIC.
    :return: html pages as rendered html
    """
    apic_ip = request.args.get('apic_ip')[8:]
    connection_status = "Current credentials are valid."
    session = login_to_apic()
    if type(session) is list:
        connection_status = session[1]

    # Render HTML
    html = base_menu()
    html += render_template('show_entercreds.html', connection_status=connection_status, apic_ip=apic_ip)
    return html


# TODO - Need to test
@app.route('/write_creds', methods=['POST'])
def write_creds():
    """
    Cache credentials used for APIC.
    :return: html pages as rendered html; Error screen on invalid data.
    """

    try:
        ipaddr = request.form['host']
        user = request.form['user']
        password = request.form['password']
        proto = request.form['proto']

    except:
        return render_error_screen("All values are required.  Please try again.")

    # Create the new credentials.py file
    try:
        credsfile = open(credsfilename, "w")
    except:
        return render_error_screen("There was a problem opening {0} Please try again.").format(credsfilename)

    credsfile.write("LOGIN = '%s'\n" % (user))
    credsfile.write("PASSWORD = '%s'\n" % (password))
    credsfile.write("IPADDR = '%s'\n" % (ipaddr))
    try:
        if proto:
            credsfile.write("URL = 'https://%s'\n" % (ipaddr))
        else:
            credsfile.write("URL = 'http://%s'\n" % (ipaddr))
        credsfile.close()
    except:
        return render_error_screen("There was a problem writing to {0} Please try again.").format(credsfilename)

    session = login_to_apic()
    if type(session) is list:
        return session[2]

    # Render HTML
    html = base_menu()
    html += render_template('entercreds_worked.html')
    return html


# TODO - Need to add tests
def get_user_tenants():
    """
    Get list of tenants from APIC and filters out 'infra' and 'mgmt'
    :return: records - List of tenant names
    """
    session = login_to_apic()
    print(session)
    if type(session) is list:
        return session[2]
    tenant_list = []
    tenants = aci.Tenant.get(session)
    for tenant in tenants:
        if tenant.name not in ('infra', 'mgmt'):
            tenant_list.append(tenant)
    return tenant_list


# TODO - Need to add tests
@app.route('/search_server')
def search_server():
    """
    Render Search for an Endpoint Page page
    :return: html pages as rendered html
    """

    # Render HTML
    tenant_list = []
    tenants = get_user_tenants()
    for tenant in tenants:
        tenant_list.append(tenant.name)

    html = base_menu()
    html += render_template('search_server.html', tenants=tenant_list)
    return html


# TODO - Need to add tests
@app.route('/search_server', methods=['POST'])
def search_server_post():
    """
    Gather data from form post and render search results
    :return: html pages as rendered html
    """
    time_start = time.time()
    session = login_to_apic()
    if type(session) is list:
        return session[2]
    try:
        tenant_name = request.form['tenant_name']
    except:     # TODO - bare except
        return render_error_screen("You must specify a tenant that you would like to search in")
    text = request.form['text']

    records = []

    tenants = get_user_tenants()
    for tenant in tenants:
        if tenant_name.upper() in tenant.name.upper() or tenant_name == 'all':
            apps = aci.AppProfile.get(session, tenant)  # TODO - aci undefined
            for local_app in apps:
                epgs = aci.EPG.get(session, local_app, tenant)    # TODO - aci undefined
                for epg in epgs:
                    # endpoints = aci.Endpoint.get_all_by_epg(session, tenant.name, app.name, epg.name, with_interface_attachments=False)
                    endpoints = c1.get_epg_info(session, tenant.name, local_app.name, epg.name)   # TODO - c1 undefined
                    for ep in endpoints:
                        for match in [ep.ip.upper(), ep.mac.upper(), ep.encap.upper(), ep.if_name.upper(),
                                      tenant.name.upper(), app.name.upper(), epg.name.upper()]:
                            if text.upper() in match:
                                records.append((ep.mac, ep.ip, ep.if_name, ep.encap,
                                                tenant.name, local_app.name, epg.name))
                                break

    html = table_header()
    html += render_template('search_server_post.html', text=text, records=set(records))
    html += table_footer()
    print('Time to complete: ', time.time() - time_start)
    return html


def get_fabric_friendly_name(url):
    """

    :param url: Full URL of APIC
    :return: Friendly name that matches URL
    """
    try:
        return app.settings.fabric_names[url]
    except KeyError:
        return url


def base_menu():
    """
    Draw initial screen and menu items.
    :return: html pages as rendered html
    """
    description = ('PGE_DC_Interface')
    # creds = aci.Credentials('apic', description)
    # args = creds.get()
    try:
        fabric = get_fabric_friendly_name(app.settings.apic_creds['url'])
    except KeyError:
        fabric = 'Not Logged In'

    header_graphic = url_for('static', filename=app.settings.header_graphic_file)
    style_wu = url_for('static', filename=app.settings.style_wu_file)

    # Render HTML
    html = render_template('menu_template.html', header_graphic=header_graphic,
                           app_title=app.settings.application_title, fabric=fabric,
                           style_guide=style_wu, fabric_names=app.settings.fabric_names)
    return html


@app.route('/addepg')
def addepg():

    rendering_file = 'addepg.html'
    page_header = "ACI Workflows - Add an EPG"
    scm_cred = Markup(source_control_credential_input())

    html = document_header()
    html += render_template(rendering_file, url_base=app.settings.url_base,
                            page_header=page_header, theme=app.settings.theme,
                            theme_cancel=app.settings.theme_cancel,
                            form_data=app.settings.form_data, cred=scm_cred)

    html += document_footer()

    return html


@app.route('/save_addepg', methods=['GET', 'POST'])
def save_addepg():
    if request.method == 'GET':
        return redirect('/', code=303)
    if "close" in request.form:
        return redirect('/', code=303)

    myepg = {}

    # Print all of the values sent to this code from the form
    # print request.form

    # New way to get the data.  Build a dictonary and make the keys the json/yml code
    # This isn't used yet
    try:
        data = request.form.to_dict()
        data["datacenter"] = clean_string(data.get("datacenter"))
        data["tenant"] = clean_string(data.get("tenant"))
        data["apppro"] = clean_string(data.get("apppro"))

        myepg["datacenter"] = clean_data(request, 'datacenter')
        myepg["tenant"] = clean_data(request, 'tenant')
        myepg["apppro"] = clean_data(request, 'apppro')
        # I'm making this all lower case however, it should be "numbers" and "."
        myepg["epgname"] = str(request.form['epgname']).lower()
        myepg["description"] = str(request.form['description'])
        myepg["legacy_vlan"] = str(request.form['legacy_vlan']).lower()

        if "bridge_domain" in request.form:
            myepg["bridge_domain"] = True
        else:
            myepg["bridge_domain"] = False

        if "default_gateway" in request.form:
            myepg["default_gateway"] = True
        else:
            myepg["default_gateway"] = False

        if "netapp_storage" in request.form:
            myepg["netapp_storage"] = True
        else:
            myepg["netapp_storage"] = False

        # Add each of the vmware vds to a list to iterate over later
        # This will allow for additions later with no refactor
        vmware_vds = []
        if "RCC_ACI" in request.form:
            vmware_vds.append("RCC_ACI")
        if "RCC_VXBLOCK_ACI" in request.form:
            vmware_vds.append("RCC_VXBLOCK_ACI")
        if "WTC_ACI" in request.form:
            vmware_vds.append("WTC_ACI")
        if "WTC_VXBLOCK_ACI" in request.form:
            vmware_vds.append("WTC_VXBLOCK_ACI")

        write_data_to_git_repo(data=myepg,
                               file_path="epgs",
                               user=request.form['SCM Username'],
                               password=request.form['SCM Password'],
                               name=request.form['SCM Name'],
                               email=request.form['SCM Email'])

    except BadRequestKeyError:
        session['message'] = index_page_message(msg="Not all form data was passed to the save page", success=False)

    return redirect(url_for('index'), code=303)


@app.route('/adducs')
def adducs():

    rendering_file = 'adducs.html'
    page_header = "ACI Workflows - Add a UCS Cluster"

    # Need to collect all data, will create some fake for know
    leafs = ["01-02", "03-04", "05-06", "07-08", "09-10", "11-12"]
    ports = list(range(1, 30))

    form_data = {"leafs": leafs, "ports": ports}

    html = document_header()
    html += render_template(rendering_file, url_base=app.settings.url_base, page_header=page_header,
                            theme=app.settings.theme, theme_cancel=app.settings.theme_cancel, form_data=form_data)
    html += document_footer()

    return html


@app.route('/save_adducs', methods=['GET', 'POST'])
def save_adducs():

    if request.method == 'GET':
        return redirect('/', code=303)
    if "close" in request.form:
        return redirect('/', code=303)

    datacenter = str(request.form['datacenter'])
    newname = str(request.form['newname'])
    description = str(request.form['description'])
    leafpair = str(request.form['leafpair'])
    port = str(request.form['port'])

    if "vpc" in request.form:
        vpc = True
    else:
        vpc = False

    # Need to add the code here to insert the new EPG
    print(datacenter, newname, description, leafpair, port, vpc)
    return redirect(url_for('index'), code=303)


@app.route('/addvxrail')
def addvxrail():
    rendering_file = 'addvxrail.html'
    page_header = "ACI Workflows - Add a VXrail Server"

    # Leafs can stay the way they are here
    leafs = ["01-02", "03-04", "05-06", "07-08", "09-10", "11-12"]

    # Need to collect all data, will create some usable for now.
    # This should be modified to collect the available ports on the selected switches above.
    # If the user selects switches 05-06, then only ports available on both of those switches
    # should be shown in this list.
    ports = list(range(1, 48))
    form_data = {"leafs": leafs, "ports": ports, "description": ""}

    html = document_header()
    scm_cred = Markup(source_control_credential_input())
    html += render_template(rendering_file, url_base=app.settings.url_base,
                            page_header=page_header, theme=app.settings.theme,
                            theme_cancel=app.settings.theme_cancel, form_data=form_data, cred=scm_cred)

    html += document_footer()

    return html


@app.route('/save_addvxrail', methods=['GET', 'POST'])
def save_addvxrail():
    if request.method == 'GET':
        return redirect('/', code=303)
    if "close" in request.form:
        return redirect('/', code=303)

    try:
        vxrail_int_selector_appendix = str(request.form['vxrail_int_selector_appendix'])
        vxrail_policy_group = str(request.form['vxrail_policy_group'])

        datacenter = clean_data(request, 'datacenter')
        # This is the interface selector name
        newname = str(request.form['newname']).lower() + vxrail_int_selector_appendix
        description = str(request.form['description'])
        leafpair = clean_data(request, 'leafpair')
        port = clean_data(request, 'port')

        output = {
            "datacenter": datacenter,
            "newname": newname,
            "description": description,
            "leafpair": leafpair,
            "port": port,
            "vxrail_policy_group": vxrail_policy_group
        }

        write_data_to_git_repo(data=output,
                               file_path="vxrail",
                               user=request.form['SCM Username'],
                               password=request.form['SCM Password'],
                               name=request.form['SCM Name'],
                               email=request.form['SCM Email'])

    except BadRequestKeyError:
        session['message'] = index_page_message(msg="Not all form data was passed to the save page", success=False)

    return redirect(url_for('index'), code=303)


def write_data_to_git_repo(data=None, file_path=None, user=None, password=None, name=None, email=None):
    repo = "pge-aci-data"
    directory = "/tmp"
    now = datetime.now()
    str_now = now.strftime("%Y%m%d-%H%M%S")
    branch_name = f"{user}-{str_now}"

    scm = SourceControlMgmt.SourceControlMgmt(username=user, friendly_name=name, email=email, password=password, repo_name=repo)
    try:
        scm.validate_scm_creds()
        scm.clone_private_repo(directory=directory)
        scm.create_new_branch_in_repo(branch_name=branch_name)
        scm.write_data_to_file_in_repo(data=data, file_path=file_path)
        scm.push_data_to_remote_repo()
        scm.delete_local_copy_of_repo()
        session['message'] = index_page_message(msg="Data successfully pushed to Source Control.",
                                                success=True, url=f'https://github.com/IGNW/{repo}/tree/{branch_name}')
    except SCMDeleteRepoError as e:
        session['message'] = index_page_message(msg=f"The repo was not deleted.  Error: '{e}'", success=False)
    except Exception as e:
        session['message'] = index_page_message(msg=f"The file was not pushed to Source Control.  Error: '{e}'", success=False)


def index_page_message(msg=None, success=None, url=None):
    if msg is None:
        msg = ''

    html = render_template('index_message.html', message=msg, success=success, url=url)
    return Markup(html)


def document_header():
    """
    Import all CSS and javascript files.  Setup page theme.
    :return: html pages as rendered html
    """

    theme_1 = url_for('static', filename=app.settings.theme_file_1)
    theme_2 = url_for('static', filename=app.settings.theme_file_2)
    css_file = url_for('static', filename='jquery.mobile.structure-1.4.5.min.css')
    jquery_file = url_for('static', filename='jquery-1.11.1.min.js')
    jquery_mobile_file = url_for('static', filename='jquery.mobile-1.4.5.min.js')

    html = render_template('document_header.html',
                           title=app.settings.application_title,
                           style_1=theme_1,
                           style_2=theme_2,
                           css=css_file,
                           jq=jquery_file,
                           jq_mobile=jquery_mobile_file
                           )

    return html


def source_control_credential_input():
    """
    Read the html from the file and prep it for use later on in the program
    """

    html = render_template('scm_cred_input.html')
    return html


def document_footer():
    """
    Close out the page.
    :return: html pages as rendered html
    """
    html = render_template('document_footer.html')
    return html


def render_error_screen(error):
    """
    Takes the error as a string, returns full html page to display
    :param error: Error code
    :return: html pages as rendered html
    """
    # Render HTML
    html = document_header()
    html += render_template('error.html', error=error)
    html += document_footer()
    return html


#  TODO - Not used
def render_success_screen(message, url):
    """
    Takes the success as a string, takes a redirect UR:, returns full html page to display
    :param message: Success message
    :param url
    :return: html pages as rendered html and redirect to url
    """
    # Render HTML
    html = document_header()
    html += render_template('success.html', message=message, url=url)
    html += document_footer()
    return html


# TODO - Not used
def get_header_graphic():
    """
    Should be included on all screens, pics a rangome graphic for the top of the screen
    :return: url_for to the graphic for the header.
    """
    header_graphic_file = header_graphic_files[random.randint(0, len(header_graphic_files)-1)]  # TODO - header_graphic_files not defined
    return url_for('static', filename=app.settings.header_graphic_file)


# TODO - Not used
def get_style_link():
    return url_for('static', filename=style_file)  # TODO - style_file not defined


# TODO - Not used
def post_url(url, data):
    # print ("post_url - {} - {}".format(url, data))
    # try:
    result = requests.post(url, headers={'Content-Type': 'application/json'}, data=(data))
    # print ("post_url - result: ".format(result.text))
    # except as e:
    #     error = "POST_URL - Application Server Failure: Not able to communicate with Application Server.  ERROR: {}".format(e)
    #     return {'result':0, 'data':render_error_screen(error)}

    decoded_json = json.loads(result.text)
    if (result.status_code == 200):
        # print ("In open url 2")
        if decoded_json['general']['status'] == 'FAIL':
            error = "Database Failure: Response from Application Server: " + decoded_json['general']['results']
            return {'result': 0, 'data': render_error_screen(error)}

        if len(decoded_json['general']['results']) == 0:
            # print ("In open url 4")
            error = "Response from Application Server: No records found."
            return {'result': 0, 'data': render_error_screen(error)}

    else:
        error = "Non 200 HTML response - Some wierd error."
        return {'result': 0, 'data': render_error_screen(error)}

    return {'result': 1, 'data': decoded_json}


def get_url(url):
    try:
        result = requests.get(url)
        # print ("In open url 1")

    except ConnectionError:
        error = "Application Server Failure: Not able to communicate with Application Server at {0} ".format(app.settings.app_addr)
        return {'result': 0, 'data': render_error_screen(error)}

    decoded_json = json.loads(result.text)
    if (result.status_code == 200):
        # print ("In open url 2")
        if decoded_json['general']['status'] == 'FAIL':
            error = "Database Failure: Response from Application Server: " + decoded_json['general']['results']
            return {'result': 0, 'data': render_error_screen(error)}

        if len(decoded_json['general']['results']) == 0:
            # print ("In open url 4")
            error = "Response from Application Server: No records found."
            return {'result': 0, 'data': render_error_screen(error)}

    else:
        error = "Non 200 HTML response - Some wierd error."
        return {'result': 0, 'data': render_error_screen(error)}

    return {'result': 1, 'data': decoded_json}


def table_header():
    """
    Should be included on all table based screens - includes the base menu
    :return: html pages as rendered html
    """
    # Render HTML
    html = base_menu()
    html += render_template('table_header.html')
    return html


def table_footer():
    """
    Should be inlcuded on all table based screens
    :return: html pages as rendered html
    """
    return render_template('table_footer.html')


if __name__ == '__main__':
    # app.secret_key = os.urandom(24)
    app.config.update(DEBUG=True)

    app.run(host='0.0.0.0', port=5000)
