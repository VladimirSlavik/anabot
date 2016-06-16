import re

import libxml2
import logging
logger = logging.getLogger('anabot')
import teres
reporter = teres.Reporter.get_reporter()

from .functions import get_attr, log_screenshot, dump
from .decorators import ACTIONS, CHECKS, handle_action, handle_check
from .actionresult import ActionResultFail, ActionResultNone, ActionResultPass

NODE_NUM = re.compile(r'\[[0-9]+\]')

RESULTS = {}

def action_result(node_path, implicit_result=ActionResultNone()):
    if isinstance(node_path, libxml2.xmlNode):
        node_path = node_path.nodePath()
    result = RESULTS.get(node_path, implicit_result)
    if isinstance(result, ActionResultNone):
        result = implicit_result
    return result

def _check_result(result):
    if result is None:
        return ActionResultNone()
    reason = None
    if type(result) == type(tuple()):
        result, reason = result
        if result:
            return ActionResultPass()
        else:
            return ActionResultFail(reason)
    elif type(result) == type(bool()):
        if result:
            return ActionResultPass()
        else:
            return ActionResultFail()
    return result

def handle_step(element, app_node, local_node):
    raw_node_path = element.nodePath()
    node_path = re.sub(NODE_NUM, '', raw_node_path)
    node_line = element.lineNo()
    policy = get_attr(element, "policy", "should_pass")
    expected_reason = get_attr(element, "fail_reason")
    handler_path = node_path
    reporter.log_info("Processing: %s" % raw_node_path)
    if handler_path not in ACTIONS:
        handler_path = None
    if policy in ("should_pass", "should_fail", "may_fail"):
        result = ACTIONS.get(handler_path)(element, app_node, local_node)
        RESULTS[raw_node_path] = _check_result(result)
    if handler_path is None:
        return
    if handler_path not in CHECKS:
        handler_path = None
    result = _check_result(CHECKS.get(handler_path)(element, app_node, local_node))
    if policy == "may_fail":
        return
    if policy in ("should_pass", "just_check"):
        if result:
            reporter.log_pass("Check passed for: %s line: %d" % (node_path, node_line))
        else:
            reporter.log_fail("Check failed for: %s line: %d" % (node_path, node_line))
    if policy in ("should_fail", "just_check_fail"):
        if not result:
            if expected_reason is None:
                reporter.log_pass("Expected failure for: %s line: %d" %
                                (node_path, node_line))
            elif expected_reason == result.fail_reason:
                reporter.log_pass("Expected failure with specified reason "
                                  "for: %s line: %d" % (node_path, node_line))
            else:
                reporter.log_fail("Wrong failure reason, expected reason "
                                  "was: %s" % expected_reason)
        else:
            reporter.log_fail("Unexpected pass for: %s line: %d" %
                              (node_path, node_line))
    if result.reason is not None:
        reporter.log_info("Reason was: %s" % result.reason)
    try:
        if result.fail_reason is not None:
            reporter.log_info("Failure reason was: %s" % result.fail_reason)
    except AttributeError:
        pass
    log_screenshot()

def default_handler(element, app_node, local_node):
    if element.name == 'debug_stop':
        from time import sleep
        import os
        RESUME_FILEPATH = '/var/run/anabot/resume'
        sleep(5)
        dump(app_node, '/tmp/dogtail.dump')
        logger.debug('DEBUG STOP at %s, touch %s to resume',
                     element.nodePath(), RESUME_FILEPATH)
        while not os.path.exists(RESUME_FILEPATH):
            sleep(0.1)
        os.remove(RESUME_FILEPATH)
    for child in element.xpathEval("./*"):
        handle_step(child, app_node, local_node)

@handle_action(None)
def unimplemented_handler(element, app_node, local_node):
    reporter.log_error('Unhandled element: %s' % element.nodePath())
    default_handler(element, app_node, local_node)

@handle_check(None)
def unimplemented_handler_check(element, app_node, local_node):
    node_path = element.nodePath()
    try:
        result = action_result(node_path)
        if result is not None:
            reporter.log_debug('Using result reported by handler for element: %s' % node_path)
            return result
    except KeyError:
        pass
    reporter.log_error('Unhandled check for element: %s' % node_path)
