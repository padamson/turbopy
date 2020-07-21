from abc import ABCMeta
from turbopy.core import PhysicsModule

def test_pif(pif_run):
    assert isinstance(PhysicsModule, ABCMeta)