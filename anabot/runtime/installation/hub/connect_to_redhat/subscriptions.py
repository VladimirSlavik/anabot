from anabot.runtime.default import default_handler
from anabot.runtime.functions import getnode, getnodes, get_attr, getsibling
from anabot.runtime.functions import TimeoutError
from anabot.runtime.translate import tr
from anabot.runtime.actionresult import ActionResultPass as Pass
from anabot.runtime.actionresult import ActionResultFail as Fail
from anabot.runtime.actionresult import NotFoundResult as NotFound
from anabot.runtime.asserts import assertLabelEquals as ale
from anabot.runtime.installation.common import done_handler

from anabot.runtime.decorators import make_prefixed_handle_action, make_prefixed_handle_check

_local_path = '/installation/hub/connect_to_redhat/registration/subscriptions'
handle_act = make_prefixed_handle_action(_local_path)
handle_chck = make_prefixed_handle_check(_local_path)

PASS = Pass()

@handle_act('')
def base_handler(element, app_node, local_node):
    local_node = getnode(local_node, "scroll pane")
    return default_handler(element, app_node, local_node)

@handle_chck('')
def base_check(element, app_node, local_node):
    ammount = get_attr(element, 'ammount')
    if ammount is None:
        ammount = len(element.xpathEval('./subscription'))
    else:
        ammount = int(ammount)
    local_node = getnode(local_node, "scroll pane")
    try:
        subscription_items = getnodes(local_node, "list item")
    except TimeoutError:
        subscription_items = []
    if len(subscription_items) != ammount:
        return Fail("Number of subscriptions displayed (%d) doesn't match expectance (%d)" % (len(subscription_items), ammount))
    subscriptions_label = getsibling(local_node, -1, "label")
    if ammount == 0:
        expected_text = "No subscriptions are attached to the system"
    elif ammount == 1:
        expected_text = "1 subscription attached to the system"
    else:
        expected_text = "%d subscriptions attached to the system" % ammount
    return ale(subscriptions_label, expected_text, "Ammount of subscriptions")

def find_subscription(local_node, name):
    try:
        subscriptions = getnodes(local_node, "list item")
    except TimeoutError:
        return None
    for list_item in subscriptions:
        if getnode(list_item, "label").name == name:
            return list_item
    return None

@handle_act('/subscription')
def subscription_handler(element, app_node, local_node):
    name = get_attr(element, "name")
    list_item = find_subscription(local_node, name)
    if list_item is None:
        return NotFound(name, where="subscriptions list")
    return default_handler(element, app_node, list_item)

@handle_chck('/subscription')
def subscription_check(element, app_node, local_node):
    name = get_attr(element, "name")
    list_item = find_subscription(local_node, name)
    if list_item is None:
        return NotFound(name, where="subscriptions list")
    return PASS

handle_act('/subscription/service_level', default_handler)
@handle_chck('/subscription/service_level')
def service_level_check(element, app_node, local_node):
    value = get_attr(element, "value")
    # UGLY HACK
    label = getnodes(local_node, "label")[5]
    return ale(label, value, "Service level")

handle_act('/subscription/sku', default_handler)
@handle_chck('/subscription/sku')
def sku_check(element, app_node, local_node):
    value = get_attr(element, "value")
    # UGLY HACK
    label = getnodes(local_node, "label")[3]
    return ale(label, value, "SKU")

handle_act('/subscription/contract', default_handler)
@handle_chck('/subscription/contract')
def contract_check(element, app_node, local_node):
    value = get_attr(element, "value")
    # UGLY HACK
    label = getnodes(local_node, "label")[1]
    return ale(label, value, "Contract")

handle_act('/subscription/start_date', default_handler)
@handle_chck('/subscription/start_date')
def start_date_check(element, app_node, local_node):
    value = get_attr(element, "value")
    # UGLY HACK
    label = getnodes(local_node, "label")[11]
    return ale(label, value, "Start date")

handle_act('/subscription/end_date', default_handler)
@handle_chck('/subscription/end_date')
def end_date_check(element, app_node, local_node):
    value = get_attr(element, "value")
    # UGLY HACK
    label = getnodes(local_node, "label")[9]
    return ale(label, value, "End date")

handle_act('/subscription/entitlements_consumed', default_handler)
@handle_chck('/subscription/entitlements_consumed')
def entitlements_consumed_check(element, app_node, local_node):
    value = get_attr(element, "value")
    # UGLY HACK
    label = getnodes(local_node, "label")[7]
    return ale(label, ("%s consumed" % value), "Entitlements consumed")

