import logging
logger = logging.getLogger('anabot')

from random import randint

from anabot.runtime.decorators import handle_action, handle_check
from anabot.runtime.default import default_handler, action_result
from anabot.runtime.functions import get_attr, getnode, getnodes, getsibling
from anabot.runtime.functions import getparents, TimeoutError
from anabot.runtime.translate import tr
from anabot.runtime.translate import oscap_tr as oscap_tr_

_local_path = '/installation/hub/oscap_addon'
handle_act = lambda x: handle_action(_local_path + x)
handle_chck = lambda x: handle_check(_local_path + x)
_chosen_profile = None
_selected_profile = None

# temporary workaround for broken translation
def oscap_tr(intext, drop_underscore=True):
    if drop_underscore:
        return(intext.replace("_", ""))
    else:
        return intext

def default_result(element):
    result = action_result(element)
    if result[0] is None:
        return (True, None)
    else:
        return result

@handle_act('')
def base_handler(element, app_node, local_node):
    logger.debug(element.nodePath())
    global _oscap_addon_visited
    try:
        oscap_addon = getnode(app_node, "spoke selector", oscap_tr("SECURITY POLICY"))
        oscap_addon.click()
    except TimeoutError:
        return (False, "Couldn't find \"SECURITY POLICY\" spoke selector")
    try:
        oscap_addon_label = getnode(app_node, "label", oscap_tr("SECURITY POLICY"))
        oscap_addon_panel = getparents(oscap_addon_label, predicates={'roleName': 'panel'})[2]
    except TimeoutError:
        return (False, "Couldn't find \"SECURITY POLICY\" label or OSCAP addon panel")
    default_handler(element, app_node, oscap_addon_panel)

@handle_chck('')
def base_check(element, app_node, local_node):
    return default_result(element)

def choose_manipulate(element, app_node, local_node, dryrun):
    mode = get_attr(element, "mode", "manual")
    try:
        profiles_label = getnode(local_node, "label", oscap_tr("Choose profile below:"))
        profiles_table = getsibling(profiles_label, 2)
    except TimeoutError:
        return (False, "Couldn't find \"Choose profile below:\" label or profiles table.")
    try:
        available_profiles = [p for p in getnodes(profiles_table, "table cell")
                            if p.text]
    except TimeoutError:
        return (False, "Couldn't find profiles (table cells)")
    profile = None # profile to be selected

    # selected profile needs to be remembered before selecting another one
    # because of check for random_strict mode
    selected_profile = [p for p in available_profiles if p.selected and p.text]
    global _chosen_profile
    if not dryrun:
        if len(selected_profile) == 0:
            _chosen_profile = None
        else:
            _chosen_profile = selected_profile[0]

    if mode == "manual":
        profile_name = get_attr(element, "profile")
        try:
            profile = [p for p in available_profiles
                    if p.name.splitlines()[0] == profile_name][0]
        except IndexError:
            return
    elif mode == "random":
        profile = available_profiles[randint(0, len(available_profiles) - 1)]
    # choose a random profile other than already selected
    elif mode == "random_strict":
        if len(available_profiles) > 1:
            if len(selected_profile) == 0:
                profile = available_profiles[randint(0, len(available_profiles) - 1)]
            elif len(selected_profile) == 1:
                profile_no = available_profiles.index(selected_profile[0])
                while profile == None or profile_no == available_profiles.index(profile):
                    profile = available_profiles[randint(0, len(available_profiles) - 1)]
        else:
            profile = available_profiles[0]
    else:
        if dryrun:
            return False
        else:
            logger.warning("Unknown selection mode: %s" % mode)
            return

    if dryrun:
        selected = lambda x: x.selected
        if mode == "manual":
            result = profile.selected
        elif mode == "random":
            result = any(map(selected, available_profiles))
        elif mode == "random_strict":
            result = any(map(selected, [p for p in available_profiles
                                        if p is not _chosen_profile]))
        else:
            result = False
        return result
    else:
        global _selected_profile
        _selected_profile = profile
        profile.click()

@handle_act('/choose')
def choose_handler(element, app_node, local_node):
    return choose_manipulate(element, app_node, local_node, False)

@handle_chck('/choose')
def choose_check(element, app_node, local_node):
    return choose_manipulate(element, app_node, local_node, True)

@handle_act('/select')
def select_handler(element, app_node, local_node):
    try:
        select_button = getnode(local_node, "push button", oscap_tr("_Select profile"),
                                sensitive=None)
    except TimeoutError:
        return (False, "Couldn't find \"Select profile\" button.")
    select_button.click()

@handle_chck('/select')
def select_check(element, app_node, local_node):
    try:
        select_button = getnode(local_node, "push button", oscap_tr("_Select profile"),
                                sensitive=False)
    except TimeoutError:
        return (False, "Couldn't find \"Select profile\" button.")

    if _selected_profile is None:
        result = (False, "No profile has been selected.")
    elif select_button.sensitive:
        result = (False, "\"Select profile\" button is sensitive.")
    elif not _selected_profile.selected:
        result = (False, "Profile \"%s\" hasn't been selected." %
                  _selected_profile.name.splitlines()[0])
    else:
        result = True
    return result

def change_content_manipulate(element, app_node, local_node, dryrun):
    change_button = getnode(local_node, "push button", oscap_tr("_Change content"))
    if dryrun:
        return default_result(element)
    else:
        change_button.click()
        try:
            getnode(local_node, "push button", oscap_tr("_Use SCAP Security Guide"))
        except TimeoutError:
            return (False, "Couldn't find \"Use SCAP Security Guide\" button.")
        default_handler(element, app_node, local_node)

@handle_act('/change_content')
def change_content_handler(element, app_node, local_node):
    return change_content_manipulate(element, app_node, local_node, False)

@handle_chck('/change_content')
def change_content_check(element, app_node, local_node):
    return change_content_manipulate(element, app_node, local_node, True)

def change_content_source_manipulate(element, app_node, local_node, dryrun):
    fetch_button = getnode(local_node, "push button", oscap_tr("_Fetch"))
    datastream_url_input = getsibling(fetch_button, -2)
    url = get_attr(element, "url")
    if dryrun:
        return datastream_url_input.text == url
    else:
        datastream_url_input.typeText(url)

@handle_act('/change_content/source')
def change_content_source_handler(element, app_node, local_node):
    return change_content_source_manipulate(element, app_node, local_node, False)

@handle_chck('/change_content/source')
def change_content_source_check(element, app_node, local_node):
    return change_content_source_manipulate(element, app_node, local_node, True)

@handle_act('/change_content/fetch')
def change_content_fetch_handler(element, app_node, local_node):
    fetch_button = getnode(app_node, "push button", oscap_tr("_Fetch"))
    fetch_button.click()

@handle_chck('/change_content/fetch')
def change_content_fetch_check(element, app_node, local_node):
    try:
        infobar = getnode(local_node, "info bar",
                          predicates={"name": tr("Error")})
        error = getnode(infobar, "label").text
        logger.info("SCAP content fetch error: \"%s\"" % error)
        result = False
    except TimeoutError:
        result = True
    return result

@handle_act('/change_content/use_ssg')
def change_content_use_ssg_handler(element, app_node, local_node):
    use_ssg_button = getnode(local_node, "push button", oscap_tr("_Use SCAP Security Guide"))
    use_ssg_button.click()

@handle_chck('/change_content/use_ssg')
def change_content_use_ssg_check(element, app_node, local_node):
    try:
        getnode(local_node, "push button", oscap_tr("_Use SCAP Security Guide"), visible=False)
        result = True
    except TimeoutError:
        result = (False, "Couldn't find \"Use SCAP Security Guide\" button.")
    return result

def apply_policy_manipulate(element, app_node, local_node, dryrun):
    policy_action = get_attr(element, "action")
    try:
        apply_policy_label = getnode(local_node, "label", oscap_tr("Apply security policy:"))
        policy_button = getsibling(apply_policy_label, 2)
    except TimeoutError:
        return (False, "Couldn't find \"Apply security policy:\" label or policy button/switch.")
    if dryrun:
        return (policy_action == "enable" and policy_button.checked
                or policy_action == "disable" and not policy_button.checked)
    else:
        if (policy_action == "enable" and not policy_button.checked
            or policy_action == "disable" and policy_button.checked):
            policy_button.click()

@handle_act('/apply_policy')
def apply_policy_handler(element, app_node, local_node):
    return apply_policy_manipulate(element, app_node, local_node, False)

@handle_chck('/apply_policy')
def apply_policy_check(element, app_node, local_node):
    return apply_policy_manipulate(element, app_node, local_node, True)

def datastream_manipulate(element, app_node, local_node, dryrun):
    datastream = get_attr(element, "id")
    mode = get_attr(element, "mode", "manual")
    try:
        ds_label = getnode(local_node, "label", oscap_tr("Data stream:"))
        ds_combo = getsibling(ds_label, 2)
        if not dryrun:
            ds_combo.click()
            ds_items = getnodes(ds_combo, "menu item")
    except TimeoutError:
        return (False,
                "Couldn't find \"Data stream:\" label or data stream combo box or menu items.")
    if dryrun:
        result = default_result(element)
        if not result[0]:
            return result
        if mode == "random":
            result = ds_combo.name != ""
        elif mode == "manual":
            result = ds_combo.name == datastream
        return result
    else:
        if mode == "manual":
            try:
                ds_item = getnode(ds_combo, "menu item", datastream)
            except TimeoutError:
                ds_combo.click()
                return (False, "Data stream '%s' not found" % datastream)
        elif mode == "random":
            ds_item = ds_items[randint(0, len(ds_items)-1)]
        ds_item.click()

@handle_act('/select_datastream')
def datastream_handler(element, app_node, local_node):
    return datastream_manipulate(element, app_node, local_node, False)

@handle_chck('/select_datastream')
def datastream_chck(element, app_node, local_node):
    return datastream_manipulate(element, app_node, local_node, True)

def checklist_manipulate(element, app_node, local_node, dryrun):
    checklist = get_attr(element, "id")
    mode = get_attr(element, "mode", "manual")
    try:
        checklist_label = getnode(local_node, "label", oscap_tr("Checklist:"))
        checklist_combo = getsibling(checklist_label, 2)
        if not dryrun:
            checklist_combo.click()
            checklist_items = getnodes(checklist_combo, "menu item")
    except TimeoutError:
        return (False, "Couldn't find \"Checklist:\" label, combo box or menu items")
    if dryrun:
        result = default_result(element)
        if not result[0]:
            return result
        if mode == "manual":
            datastream = get_attr(element, "id")
            try:
                checklist_label = getnode(local_node, "label", oscap_tr("Checklist:"))
                checklist_combo = getsibling(checklist_label, 2)
            except TimeoutError:
                return (False, "Couldn't find \"Checklist:\" label or combo box.")
            result = checklist_combo.name == datastream
        elif mode == "random":
            return checklist_combo.name != ""
        return result
    else:
        if mode == "manual":
            try:
                checklist_item = getnode(checklist_combo, "menu item", checklist)
            except TimeoutError:
                checklist_combo.click()
                return(False, "Checklist \"%s\" not found" % checklist)
        elif mode == "random":
            checklist_item = checklist_items[randint(0, len(checklist_items)-1)]
        else:
            return (False, "Unknown mode: \"%s\"" % mode)
        checklist_item.click()

@handle_act('/select_checklist')
def checklist_handler(element, app_node, local_node):
    return checklist_manipulate(element, app_node, local_node, False)

@handle_chck('/select_checklist')
def checklist_check(element, app_node, local_node):
    return checklist_manipulate(element, app_node, local_node, True)

@handle_act('/done')
def done_handler(element, app_node, local_node):
    try:
        done_button = getnode(local_node, "push button", tr("_Done", False))
    except TimeoutError:
        logger.debug([str(x) for x in getnodes(local_node, "push button")])
        logger.debug(tr("_Done"))
        return (False, "Couldn't find \"Done\" button.")
    done_button.click()

@handle_chck('/done')
def done_check(element, app_node, local_node):
    result = default_result(element)
    if result[0]:
        try:
            oscap_addon_selector = getnode(app_node, "spoke selector",
                                        oscap_tr("SECURITY POLICY"))
            oscap_addon_status = getnode(oscap_addon_selector, "label").text
            if not oscap_addon_status == oscap_tr_("Everything okay"):
                return(False, "OSCAP addon status: \"%s\"" % oscap_addon_status)
        except TimeoutError as e:
            return(False, "OSCAP addon selector button or status label not found: %s" % e)
    return result

