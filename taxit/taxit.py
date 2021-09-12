
import pandas as pd
from taxit.helpers import classproperty


class TaxRates(object):

    def __init__(self, marital_status):

        self._marital_status=marital_status

    @property
    def federal(self):

        if self._marital_status=='single':
            return pd.DataFrame([
                [0,       9875,      10],
                [9876,    40125,     12],
                [40126,   85525,     22],
                [85526,   163300,    24],
                [163301,  207350,    32],
                [207351,  518400,    35],
                [518401,  999999999, 37]
            ], columns=['start', 'end', 'rate'])


        if self._marital_status=='married':
            return pd.DataFrame([
                [0,       19750,     10],
                [19750,   80250,     12],
                [80251,   171050,    22],
                [171051,  326600,    24],
                [326601,  414700,    32],
                [414701,  622050,    35],
                [622051,  999999999, 37]
            ], columns=['start', 'end', 'rate'])

    @property
    def ssi(self):

        if self._marital_status=='single':
            return pd.DataFrame([
                [0,       137700,    6.2],
                [137701,  200000,    0.0],
                [200001,  999999999, 0.9],
            ], columns=['start', 'end', 'rate'])

        if self._marital_status=='married':
            return pd.DataFrame([
                [0,       137700,    6.2],
                [137701,  250000,    0.0],
                [250001,  999999999, 0.9],
            ], columns=['start', 'end', 'rate'])

    @property
    def medicare(self):

        if self._marital_status=='single':
            return pd.DataFrame([
                [0,       200000,    1.45],
                [200001,  999999999, 2.35],
            ], columns=['start', 'end', 'rate'])

        if self._marital_status=='married':
            return pd.DataFrame([
                [0,       250000,    1.45],
                [250001,  999999999, 2.35],
            ], columns=['start', 'end', 'rate'])

    @property
    def cap_gains_long(self):

        if self._marital_status=='single':
            return pd.DataFrame([
                [0,       40000,     0],
                [40001,   441450,    15],
                [441451,  999999999, 20],
            ], columns=['start', 'end', 'rate'])

        if self._marital_status=='married':
            return pd.DataFrame([
                [0,       80000,     0],
                [80001,   496600,    15],
                [496601,  999999999, 20],
            ], columns=['start', 'end', 'rate'])
