# -*- coding: utf-8 -*-
import logging
logger = logging.getLogger('anabot')

import os, shutil, subprocess, stat

def _hooks(event):
    hooks_dir = os.path.join('/', 'opt', 'anabot-hooks', event)
    for hook in os.listdir(hooks_dir):
        yield os.path.join(hooks_dir, hook)

def _run_hooks(hooks, chroot=None, preexec_fn=None):
    preexec = preexec_fn
    if chroot is not None:
        def tmp_preexec():
            if preexec_fn is not None:
                preexec_fn()
            os.chroot(chroot)
        preexec = tmp_preexec
    for hook in hooks:
        exec_path = hook
        os.chmod(exec_path, stat.S_IEXEC)
        if chroot is not None:
            new_path = os.path.join(chroot, 'tmp', os.path.basename(hook))
            shutil.copy(hook, new_path)
            exec_path = os.path.join('/', 'tmp', os.path.basename(hook))
            logger.debug("Copying hook for chroot to: %s", new_path)
            logger.debug("Running hook (in chroot %s): %s", chroot, exec_path)
        else:
            logger.debug("Running hook: %s", exec_path)
        p = subprocess.Popen([exec_path], preexec_fn=preexec)
        p.wait()
        if chroot is not None:
            logger.debug("Removing hook from chroot: %s", new_path)
            os.unlink(new_path)

def run_prehooks():
    _run_hooks(_hooks('pre'))

def run_postnochroothooks():
    _run_hooks(_hooks('post-nochroot'))

def run_posthooks():
    _run_hooks(_hooks('post'), chroot='/mnt/sysimage')
