import time

import teres
reporter = teres.Reporter.get_reporter()

from anabot.runtime.decorators import handle_action, handle_check, check_action_result
from anabot.runtime.default import default_handler, action_result
from anabot.runtime.functions import getnode, getnodes, get_attr, getparents, getsibling, disappeared
from anabot.runtime.functions import getnode_scroll, handle_checkbox, check_checkbox, is_alive
from anabot.runtime.functions import TimeoutError
from anabot.runtime.translate import tr
from anabot.runtime.actionresult import ActionResultPass as Pass
from anabot.runtime.actionresult import ActionResultFail as Fail
from anabot.runtime.actionresult import NotFoundResult as NotFound
from anabot.runtime.asserts import assertTextInputEquals as atie
from anabot.runtime.asserts import assertPasswordTextInputEquals as aptie
from anabot.runtime.installation.common import done_handler
from anabot.conditions import is_distro_version

from anabot.runtime.decorators import make_prefixed_handle_action, make_prefixed_handle_check

from . import options, registration

_local_path = '/installation/hub/connect_to_redhat'
handle_act = make_prefixed_handle_action(_local_path)
handle_chck = make_prefixed_handle_check(_local_path)


PASS = Pass()
SPOKE_SELECTOR_NOT_FOUND = NotFound("active spoke selector",
                                    "selector_not_found",
                                    whose="Connect to Red Hat")
SPOKE_NOT_FOUND = NotFound("panel",
                           "spoke_not_found",
                           whose="Connect to Red Hat")
DONE_NOT_FOUND = NotFound('"Done" button',
                          "done_not_found",
                          where="Connect to Red Hat")


@handle_act('')
def base_handler(element, app_node, local_node):
    spoke_selector_text = tr("_Connect to Red Hat", context="GUI|Spoke")

    try:
        spoke_selector = getnode_scroll(
            app_node, "spoke selector", spoke_selector_text
        )
    except TimeoutError:
        return SPOKE_SELECTOR_NOT_FOUND

    spoke_selector.click()

    try:
        spoke_label = getnode(app_node, "label", tr("CONNECT TO RED HAT"))
    except TimeoutError:
        if is_distro_version('rhel', 8, 2):
            try:
                spoke_label = getnode(app_node, "label", tr("CONNECT TO REDHAT"))
                reporter.log_fail("Label containing 'REDHAT' found: https://bugzilla.redhat.com/show_bug.cgi?id=1787342")
            except TimeoutError:
                return SPOKE_NOT_FOUND
        else:
            return SPOKE_NOT_FOUND

    local_node = getparents(spoke_label, "panel")[2]
    default_handler(element, app_node, local_node)

    # Click the Done button.
    try:
        done_handler(element, app_node, local_node)
        return PASS
    except TimeoutError:
        return DONE_NOT_FOUND

@handle_chck('')
@check_action_result
def base_check(element, app_node, local_node):
    try:
        disappeared(app_node, "label", tr("CONNECT TO REDHAT"))
        return PASS
    except TimeoutError:
        return Fail("Connect to Red Hat spoke is still visible.")

def auth_radio(local_node, auth_type):
    radio = {
        'account' : getnode(local_node, 'radio button', tr('_Account', context='GUI|Subscription|Authentication|Account')),
        'activation key' : getnode(local_node, 'radio button', tr('Activation _Key', context='GUI|Subscription|Authetication|Activation Key'))
    }
    return radio[auth_type]

@handle_act('/authentication')
def auth_handler(element, app_node, local_node):
    auth_type = get_attr(element, 'type')
    try:
        auth_radio(local_node, auth_type).click()
    except KeyError:
        return Fail('Auth type "%s" is not available.' % auth_type)
    return PASS

@handle_chck('/authentication')
def auth_check(element, app_node, local_node):
    auth_type = get_attr(element, 'type')
    try:
        return auth_radio(local_node, auth_type).checked
    except KeyError:
        return Fail('Auth type "%s" is not available.' % auth_type)

def rhsm_credentials_panel(local_node):
    # DIRTY HACK
    # Panel with username and password is the first one before 'Authentication' label
    auth_label = getnode(local_node, 'label', tr('Authentication'))
    return getsibling(auth_label, -1, 'panel')

@handle_act('/username')
def username_handler(element, app_node, local_node):
    local_node = rhsm_credentials_panel(local_node)
    value = get_attr(element, 'value')
    # DIRTY HACK
    # Username input is the first text in the credentials panel
    getnode(local_node, 'text').typeText(value)
    return PASS

@handle_chck('/username')
def username_check(element, app_node, local_node):
    local_node = rhsm_credentials_panel(local_node)
    value = get_attr(element, 'value')
    # DIRTY HACK
    # Username input is the first text in the credentials panel
    return atie(getnode(local_node, 'text'), value, "Username")

@handle_act('/password')
def password_handler(element, app_node, local_node):
    local_node = rhsm_credentials_panel(local_node)
    value = get_attr(element, 'value')
    # DIRTY HACK
    # Password input is the first password in the credentials panel
    getnode(local_node, 'password text').typeText(value)
    return PASS

@handle_chck('/password')
def password_check(element, app_node, local_node):
    local_node = rhsm_credentials_panel(local_node)
    value = get_attr(element, 'value')
    # DIRTY HACK
    # Password input is the first password in the credentials panel
    return aptie(getnode(local_node, 'password text'), value, 'Account')

def rhsm_activation_panel(local_node):
    # DIRTY HACK
    # Panel with organization and activation key is the second one before 'Authentication' label
    auth_label = getnode(local_node, 'label', tr('Authentication'))
    return getsibling(auth_label, -2, 'panel')

@handle_act('/organization')
def organization_handler(element, app_node, local_node):
    local_node = rhsm_activation_panel(local_node)
    value = get_attr(element, 'value')
    # DIRTY HACK
    # Organization is second text in activation panel
    getnodes(local_node, 'text')[1].typeText(value)
    return PASS

@handle_chck('/organization')
def organization_check(element, app_node, local_node):
    local_node = rhsm_activation_panel(local_node)
    value = get_attr(element, 'value')
    # DIRTY HACK
    # Organization is second text in activation panel
    return atie(getnodes(local_node, 'text')[1], value, "Organization")

@handle_act('/activation_key')
def activation_key_handler(element, app_node, local_node):
    local_node = rhsm_activation_panel(local_node)
    value = get_attr(element, 'value')
    # DIRTY HACK
    # Activation key is first text in activation panel
    getnodes(local_node, 'text')[0].typeText(value)
    return PASS

@handle_chck('/activation_key')
def activation_key_check(element, app_node, local_node):
    local_node = rhsm_activation_panel(local_node)
    value = get_attr(element, 'value')
    # DIRTY HACK
    # Activation key is first text in activation panel
    return atie(getnodes(local_node, 'text')[0], value, "Activation key")

def system_purpose(local_node):
    return getnode(local_node, 'check box', tr('Set System Purpose', context='GUI|Subscription|Set System Purpose'))

# Note: valid values for system purpose are available in /etc/rhsm/syspurpose/valid_fields.json

@handle_act('/system_purpose')
def system_purpose_handler(element, app_node, local_node):
    set_purpose = get_attr(element, 'set')
    checkbox = system_purpose(local_node)
    if set_purpose is not None and checkbox.checked != (set_purpose == 'yes'):
        checkbox.click()
    system_purpose_panel = getsibling(checkbox, 1, 'panel')
    default_handler(element, app_node, system_purpose_panel)
    return PASS

@handle_chck('/system_purpose')
def system_purpose_check(element, app_node, local_node):
    set_purpose = get_attr(element, 'set')
    checkbox = system_purpose(local_node)
    if set_purpose is not None and checkbox.checked != (set_purpose == 'yes'):
        return Fail('"Set System Purpose" checkbox is not in desired state.')
    return PASS

def combo_str(value):
    if value is None:
        return tr('Not Specified')
    return value

def purpose_combo_handler(element, app_node, local_node, index, name):
    role = combo_str(get_attr(element, 'value'))
    role_combobox = getnodes(local_node, 'combo box')[index]
    if role_combobox.name != role:
        role_combobox.click()
        combo_window = getnode(app_node, "window")
        getnode(combo_window, "menu item", role).click()
    return PASS

def purpose_combo_check(element, app_node, local_node, index, name):
    value = combo_str(get_attr(element, 'value'))
    combobox = getnodes(local_node, 'combo box')[index]
    if combobox.name != value:
        return Fail('Different %s value was present: "%s". Expected: "%s".' % (name, combobox.name, value))
    return PASS

@handle_act('/system_purpose/role')
def system_purpose_role_handler(element, app_node, local_node):
    return purpose_combo_handler(element, app_node, local_node, 2, 'role')

@handle_chck('/system_purpose/role')
def system_purpose_role_check(element, app_node, local_node):
    return purpose_combo_check(element, app_node, local_node, 2, 'role')

@handle_act('/system_purpose/sla')
def system_purpose_sla_handler(element, app_node, local_node):
    return purpose_combo_handler(element, app_node, local_node, 1, 'sla')

@handle_chck('/system_purpose/sla')
def system_purpose_sla_check(element, app_node, local_node):
    return purpose_combo_check(element, app_node, local_node, 1, 'sla')

@handle_act('/system_purpose/usage')
def system_purpose_usage_handler(element, app_node, local_node):
    return purpose_combo_handler(element, app_node, local_node, 0, 'usage')

@handle_chck('/system_purpose/usage')
def system_purpose_usage_check(element, app_node, local_node):
    return purpose_combo_check(element, app_node, local_node, 0, 'usage')

@handle_act('/insights')
def insights_handler(element, app_node, local_node):
    checkbox = getnode(local_node, "check box", tr("Connect to Red Hat _Insights", context="GUI|Subscription|Red Hat Insights"))
    return handle_checkbox(checkbox, element)

@handle_chck('/insights')
def insights_check(element, app_node, local_node):
    checkbox = getnode(local_node, "check box", tr("Connect to Red Hat _Insights", context="GUI|Subscription|Red Hat Insights"))
    return check_checkbox(checkbox, element, 'Connect to Red Hat Insights')

@handle_act('/register')
def register_handler(element, app_node, local_node):
    button = getnode(local_node, "push button", tr("_Register", context="GUI|Subscription|Register"))
    button.click()
    return PASS

@handle_chck('/register')
def register_check(element, app_node, local_node):
    button = getnode(local_node, "push button", tr("_Register", context="GUI|Subscription|Register"), sensitive=None, visible=None)
    if not button.sensitive or not button.visible:
        return PASS
    return Fail("Register button is clickable and visible")

def unregister_button(local_node, visible=True, sensitive=True):
    return getnode(local_node, "push button", tr("_Unregister", context="GUI|Subscription|Unregister"), visible=visible, sensitive=sensitive)

not_registered = "Not registered."
register_phases = [
    "Registering...",
    "Attaching subscription..."
]
registered = "Registered."

@handle_act('/wait_until_registered')
def wait_until_registered_handler(element, app_node, local_node):
    register_button = getnode(local_node, "push button", tr("_Register", context="GUI|Subscription|Register"), sensitive=None, visible=None)
    status_label = getsibling(register_button, -1, "label", sensitive=None)
    tr_register_phases = [ tr(phase) for phase in register_phases ]
    while status_label.name in tr_register_phases or not is_alive(status_label):
        if not is_alive(status_label):
            reporter.log_info("Registration status label is not alive!")
            time.sleep(1)
            continue
        reporter.log_info("Registration status is: %s" % status_label.name)
        time.sleep(1)
    reporter.log_info("Registration status is: %s" % status_label.name)
    return PASS

@handle_act('/unregister')
def unregister_handler(element, app_node, local_node):
    unregister_button = getnode(local_node, "push button", tr("_Unregister", context="GUI|Subscription|Unregister"))
    unregister_button.click()
    return PASS

@handle_chck('/unregister')
def unregister_check(element, app_node, local_node):
    if disappeared(local_node, "push button", tr("_Unregister", context="GUI|Subscription|Unregister")):
        return PASS
    return Fail("Unregister button is clickable and visible")
