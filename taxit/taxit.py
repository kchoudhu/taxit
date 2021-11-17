__all__ = [
    'Family',
    'Person',
    'Company',
    'TaxingEntity'
]

import pandas as pd
from taxit.helpers import classproperty

class Account(object):

    def __init__(self, name, account_type=None, affiliated_with=None):

        repr_name = name
        if affiliated_with is not None:
            repr_name = f"{repr_name}_{affiliated_with.name.lower().replace(' ', '_')}"
        self.name = repr_name

        self.account_type = account_type

        self.affiliated_with = affiliated_with

        self.grid = pd.DataFrame([], columns=['description', 'amount'])


    def __repr__(self):

        return f"<{self.__module__}.{self.__class__.__name__} at {hex(id(self))}: {self.name}>"


    def __str__(self):

        return str(self.grid)


class TaxableRoot(object):

    def __init__(self, name, taxed_by):

        self.name = name

        self.accounts = {}

        self.add_account('general')

        for taxing_entity in taxed_by:
            self.add_account(taxing_entity.name)


    def add_account(self, account_name, account_type=None, affiliated_with=None):

        account = Account(account_name, account_type=account_type, affiliated_with=affiliated_with)
        self.accounts[account.name] = account


    def transfer(self, from_account, to, to_account, amount, description=None):

        self.accounts[from_account].grid.loc[-1] = [description, -amount]
        self.accounts[from_account].grid.index += 1

        to.accounts[to_account].grid.loc[-1] = [description, amount]
        to.accounts[to_account].grid.index += 1


class TaxingEntity(TaxableRoot):

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

        super().__init__(jurisdiction, [])

        self.schedule = {
            'usa' : self.US_Rates
        }[self.name]


    def __repr__(self):

        return f"<{self.__module__}.{self.__class__.__name__} at {hex(id(self))}: {self.name}>"


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

    def __init__(self, name, family=None, is_child=False, taxed_by=[], f_eie=False, f_housing=False):

        super().__init__(name, taxed_by)

        self.is_child = is_child
        if family is not None:
            if is_child is True:
                family.add_child(self)
            else:
                family.add_parent(self)


    def __repr__(self):

        return f"<{self.__class__.__module__}.{self.__class__.__name__} at {hex(id(self))}: {self.name}>"


class Company(TaxableRoot):

    def __init__(self, name, taxed_by=[], owned_by={}):

        super().__init__(name, taxed_by)

        self.ownership = owned_by
        self.employees = {}


    def __repr__(self):

        return f"<{self.__class__.__module__}.{self.__class__.__name__} at {hex(id(self))}: {self.name}>"


    def employs(self, person, _401k=False, child_care=False):

        self.employees[person.name] = person

        if _401k is True:
            person.add_account('401k', account_type='401k', affiliated_with=self)

        if child_care is True:
            person.add_account('child_care', affiliated_with=self)


    def pay_contract(self, to, amount):

        self.transfer('general', to, 'general', amount, description='contract')


    def pay_salary(self, to, amount, _401k=0):

        pass


    def share_profits(self, to, amount, percentage):

        pass


    def pay_dividends(self):

        pass
