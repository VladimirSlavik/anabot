class ActionResult(object):
    result = None
    reason = None

    def __init__(self):
        if self.__class__  == ActionResult:
            raise NotImplementedError("Abstract base class 'ActionResult' "
                                      "can't be instantiated.")

    def __eq__(self, other):
        if type(other) == bool or other is None:
            return self.result == other
        elif (type(other) == tuple and len(other) == 2
                and (type(other[0]) == bool or other[0] is None)
                and (type(other[1]) == str or other[1] is None)):
            return other[0] == self.result and other[1] == self.reason
        elif isinstance(other, ActionResult):
            return (other.result == self.result
                    and other.reason == self.reason)
        else:
            raise TypeError("Unable to compare objects of types '%s' and '%s'." %
                            (self.__class__.__name__,
                             other.__class__.__name__))

    def __getitem__(self, index):
        if index == 0:
            return self.result
        elif index == 1:
            return self.reason
        else:
            raise IndexError("No such item: %d" % index)


class ActionResultPass(ActionResult):
    result = True


class ActionResultFail(ActionResult):
    result = False

    def __init__(self, reason=None, fail_reason=None):
        self.reason = reason
        self.fail_reason = fail_reason

    def __eq__(self, other):
        if (isinstance(other, ActionResult)
                and self.fail_reason != other.fail_reason):
            return False
        return super(ActionResultFail, self).__eq__(other)


class ActionResultNone(ActionResult):
    pass

