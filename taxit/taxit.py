__all__ = [
    'Family',
    'Person',
    'Company',
    'TaxingEntity'
]

import pandas as pd
from taxit.helpers import classproperty

class TaxingEntity(object):


    class US_Rates(object):

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


    def __init__(self, jurisdiction):

        self.jurisdiction = jurisdiction

        self.schedule = {
            'USA' : self.US_Rates
        }[self.jurisdiction]


    def __repr__(self):

        return f"<{self.__module__}.{self.__class__.__name__} at {hex(id(self))}: {self.jurisdiction}>"


    def create_account(self, taxable_entity):

        print(f"Creating account with [{self.jurisdiction}] for [{taxable_entity.name}]")


class TaxableRoot(object):


    def __init__(self, name, taxed_by):

        self.name = name

        # Create an account for this TaxableEntity
        # in each taxed_by
        for entity in taxed_by:
            entity.create_account(self)


class Family(TaxableRoot):

    def __init__(self, name, taxed_by=[]):

        self.parents  = {}
        self.children = {}

        super().__init__(name, taxed_by)


    def __repr__(self):

        return f"<{self.__module__}.{self.__class__.__name__} at {hex(id(self))}: {self.name}>"


    @property
    def members(self):

        return {**self.parents, **self.children}


    def add_parent(self, parent):

        if parent.name not in self.parents:
            self.parents[parent.name] = parent

        return self


    def add_child(self, child):

        if child.name not in self.children:
            self.children[child.name] = child

        return self


class Person(TaxableRoot):

    def __init__(self, name, is_child=False, taxed_by=[]):

        self.name = name
        self.is_child = is_child

        super().__init__(name, taxed_by)


    def works_at(self, company):

        self.employer = company

        return self


    def __repr__(self):

        return f"<{self.__class__.__module__}.{self.__class__.__name__} at {hex(id(self))}: {self.name}>"


class Company(TaxableRoot):

    def __init__(self, name, taxed_by=[], owned_by={}):

        self.name = name

        self.ownership = owned_by

        super().__init__(name, taxed_by)


    def pay_salary(self, amount):

        pass


    def pay_profit_share(self, amount, percentage):

        pass


    def pay_dividend(self):

        pass


    def receive_income(self):

        pass
