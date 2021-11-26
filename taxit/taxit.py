__all__ = [
    'Family',
    'Person',
    'Company',
    'TaxingEntity'
]

import pandas as pd
from taxit.helpers import classproperty

class Account(object):

    def __init__(self, name, account_type=[], affiliated_with=None, generate_name=False):

        repr_name = name
        if generate_name is True:
            repr_name = f"{affiliated_with.name.lower().replace(' ', '_')}.{repr_name}"
        self.name = repr_name

        self.account_type = set([t.strip() for t in account_type])

        self.affiliated_with = affiliated_with

        self.grid = pd.DataFrame([], columns=['description', 'for_benefit_of', 'cross_entity', 'cross_account', 'amount'])


    @property
    def value(self):

        return self.grid['amount'].sum()

    def __repr__(self):

        return f"<{self.__module__}.{self.__class__.__name__} at {hex(id(self))}: {self.name} ${round(self.value,2)}>"


    def __str__(self):

        return str(self.grid)


    def __add__(self, b):

        return self.__radd__(b)


    def __radd__(self, b):

        acct = Account('tmp')

        if type(b)!=int:
            acct.grid = self.grid.append(b.grid)
        else:
            acct.grid = self.grid.copy(deep=True)

        return acct


class TaxableRoot(object):

    def __init__(self, name, taxed_by):

        self.name = name

        self.accounts = {}

        self.add_account('general')

        for taxing_entity in taxed_by:

            self.rates = taxing_entity.rate_schedule(for_entity=self)

            self.add_account(taxing_entity.accounts['general'], name=taxing_entity.name)


    def __getitem__(self, idx):

        if type(idx) == str:
            return self.accounts[idx].grid

        return super().__getitem__(idx)


    @property
    def marital_status(self): return 'single'


    def add_account(self, account, name=None, account_type=[], affiliated_with=None, generate_name=False):

        if not isinstance(account, Account):
            if affiliated_with is None:
                affiliated_with = self
            account = Account(account, account_type=account_type, affiliated_with=affiliated_with, generate_name=generate_name)

        self.accounts[account.name if name is None else name] = account


    def transfer(self, from_account, to, amount, description=None, for_benefit_of=None):

        fbo_name = None
        if for_benefit_of is not None:
            fbo_name = for_benefit_of.name

        self.accounts[from_account].grid.loc[-1] = [description, fbo_name, to.affiliated_with.name, to.name,   -amount]
        self.accounts[from_account].grid.index += 1

        to.grid.loc[-1] = [description, fbo_name, self.name, from_account, amount]
        to.grid.index += 1


class TaxingEntity(TaxableRoot):

    class US_Rates(object):
        """
        All rates 2021
        """

        def __init__(self, for_entity=None, year=2020):

            self.entity = for_entity

            self.year = year

            if self.entity is not None:
                self.marital_status=self.entity.marital_status
            else:
                self.marital_status='single'


        @property
        def max_401k(self):

            df = pd.DataFrame([
                19500,
                38500,
                58000
            ], columns=['amount'])

            df.index = ['employee', 'employer', 'total']

            return df

        @property
        def max_child_care(self):

            df = pd.DataFrame([
                5000
            ], columns=['amount'])

            df.index = ['total']

            return df


        @property
        def federal(self):

            if self.marital_status=='single':
                return pd.DataFrame([
                    [0,       9950,      10],
                    [9950,    40525,     12],
                    [40525,   86375,     22],
                    [86375,   164925,    24],
                    [164925,  209425,    32],
                    [209425,  523600,    35],
                    [523600,  999999999, 37]
                ], columns=['start', 'end', 'rate'])


            if self.marital_status=='married':
                return pd.DataFrame([
                    [0,       19900,     10],
                    [19900,   81050,     12],
                    [81050,   172750,    22],
                    [172750,  329850,    24],
                    [329850,  418850,    32],
                    [418850,  628300,    35],
                    [628300,  999999999, 37]
                ], columns=['start', 'end', 'rate'])


        @property
        def ssi_employer(self):

            return pd.DataFrame([
                [0,       142800,    6.2],
                [142800,  999999999, 0.0],
            ], columns=['start', 'end', 'rate'])


        @property
        def ssi_employee(self):

            return self.ssi_employer


        @property
        def medicare_employer(self):

            return pd.DataFrame([
                [0,       999999999,    1.45],
            ], columns=['start', 'end', 'rate'])


        @property
        def medicare_employee(self):

            return pd.DataFrame([
                [0,       200000,       1.45],
                [200000,  999999999,    2.35],
            ], columns=['start', 'end', 'rate'])


        @property
        def medicare_surtax(self):

            if self.marital_status=='married':
                return pd.DataFrame([
                    [0,       250000,    1.45],
                    [250000,  999999999, 2.35],
                ], columns=['start', 'end', 'rate'])
            else:
                return self.medicare_employee


        @property
        def cap_gains_long(self):

            if self.marital_status=='single':
                return pd.DataFrame([
                    [0,       40000,     0],
                    [40001,   441450,    15],
                    [441451,  999999999, 20],
                ], columns=['start', 'end', 'rate'])

            if self.marital_status=='married':
                return pd.DataFrame([
                    [0,       80000,     0],
                    [80001,   496600,    15],
                    [496601,  999999999, 20],
                ], columns=['start', 'end', 'rate'])


        def apply(self, amount, schedule, table=False):

            w2_so_far = self.entity.highwater('w2', account='general')

            new_taxable_amount = w2_so_far + amount

            df = getattr(self, schedule)

            ind = df.index[(df['start'] < new_taxable_amount) & (amount < df['end'])]
            df.loc[ind, 'amount'] = new_taxable_amount-df.loc[ind, 'start']

            ind = df.index[new_taxable_amount > (df['end'])]
            df.loc[ind, 'amount'] = df.loc[ind, 'end']-df.loc[ind, 'start']

            ind = df.index[df['start'] > new_taxable_amount]
            df.loc[ind, 'amount'] = 0

            df['tax'] = df['amount']*df['rate']/100

            schedule_so_far = self.entity.highwater(schedule)

            return df if table is True else sum(df['tax'])-schedule_so_far


    def __init__(self, jurisdiction):

        super().__init__(jurisdiction, [])

        self.rate_schedule = {
            'usa' : self.US_Rates
        }[jurisdiction]

        self.rates = self.rate_schedule()


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

        parent.martial_status = 'married'

        return self


    def add_child(self, child):

        if child.name not in self.children:
            self.children[child.name] = child

        return self


class Person(TaxableRoot):

    def __init__(self, name, family=None, is_child=False, taxed_by=[], f_eie=False, f_housing=False):

        super().__init__(name, taxed_by)

        self.f_eie = f_eie
        self.f_housing = f_housing

        self.is_child = is_child
        if family is not None:
            if is_child is True:
                family.add_child(self)
            else:
                family.add_parent(self)


    def __repr__(self):

        return f"<{self.__class__.__module__}.{self.__class__.__name__} at {hex(id(self))}: {self.name}>"


    def find_account(self, affiliated_with, account_type):

        if affiliated_with is None:
            return [acct for acct in self.accounts.values() if (account_type in acct.account_type)]
        else:
            x = [acct for acct in self.accounts.values() if (acct.affiliated_with==affiliated_with and account_type in acct.account_type)]
            return None if len(x)==0 else x[0]


    @property
    def pretax_accounts(self):

        accts = {}

        pretax_acct_types = {'401k', '403b', 'child_care'}

        for acct_name, acct in self.accounts.items():

            if len(pretax_acct_types-acct.account_type)!=len(pretax_acct_types):
                accts[acct_name] = acct

        return list(accts.values())


    @property
    def retirement_accounts(self):

        accts = {}

        for acct_name, acct in self.accounts.items():
            if 'retirement' in acct.account_type:
                accts[acct_name] = acct

        return list(accts.values())


    def highwater(self, measure, account='usa'):

        df = self.accounts[account].grid

        df = df[(df['description']==measure) & (df['for_benefit_of']==self.name)]

        # Return abs here -- we may be referring to
        # negative flows
        return abs(df['amount'].sum())


class Company(TaxableRoot):

    def __init__(self, name, taxed_by=[], owned_by={}):

        super().__init__(name, taxed_by)

        self.ownership = owned_by
        self.employees = {}


    def __repr__(self):

        return f"<{self.__class__.__module__}.{self.__class__.__name__} at {hex(id(self))}: {self.name}>"


    def employs(self, person, _403b=False, _401k=False, child_care=False):

        self.employees[person.name] = person

        if _403b is True:
            person.add_account('403b', account_type=['403b', 'retirement'], affiliated_with=self, generate_name=True)

        if _401k is True:
            person.add_account('401k', account_type=['401k', 'retirement'], affiliated_with=self, generate_name=True)

        if child_care is True:
            person.add_account('child_care', account_type=['child_care'], affiliated_with=self, generate_name=True)


    def pay_contract(self, to, amount):

        self.transfer('general', to.accounts['general'], amount, description='contract')


    def pay_salary(self, to, amount, _403b=0, _403b_match=0, _401k=0, _401k_match=0, child_care=0):

        # Employer FICA
        employer_ssi = to.rates.apply(amount, 'ssi_employer')
        employer_mc  = to.rates.apply(amount, 'medicare_employer')
        self.transfer('general', self.accounts['usa'], employer_ssi, description='ssi_employer', for_benefit_of=to)
        self.transfer('general', self.accounts['usa'], employer_mc, description='medicare_employer', for_benefit_of=to)

        # Employee FICA
        employee_ssi = to.rates.apply(amount, 'ssi_employee')
        employee_mc = to.rates.apply(amount, 'medicare_employee')
        to.transfer('general', to.accounts['usa'], employee_ssi, description='ssi_employee', for_benefit_of=to)
        to.transfer('general', self.accounts['usa'], employee_mc, description='medicare_employee', for_benefit_of=to)

        # Deposit salary
        self.transfer('general', to.accounts['general'], amount, description='w2', for_benefit_of=to)


        # Let's make sure retirement numbers make sense
        if _403b+child_care+_401k > amount:
            raise Exception(f"Pretax deductions of {_403b+_401k+child_care} cannot be more than salary {amount}")

        # Add money to 403b if any
        account_403b = to.find_account(self, '403b')
        if account_403b is not None:
            if _403b>0:
                to.transfer('general', account_403b, _403b, description=f'403b contribution', for_benefit_of=to)

            if _403b_match>0:
                self.transfer('general', account_403b, _403b_match, description=f'403b employer match', for_benefit_of=to)

        # 403b is poison -- it reduces the available tax space
        # for all pre-tax accounts to that of one employer space
        max_retirement = to.rates.max_401k.loc['total'].amount
        accounts_403b = to.find_account(None, '403b')
        value_403b = 0 if len(accounts_403b)==0 else sum(accounts_403b).value
        if value_403b>0:
            max_retirement -= sum(to.retirement_accounts).value

        account_401k = to.find_account(self, '401k')
        if account_401k is not None:

            if max_retirement<(_401k+_401k_match):
                raise Exception(f"401k contribution {_401k+_401k_match} is greater than remaining retirement space {max_retirement}")

            if _401k>0:
                to.transfer('general', account_401k, _401k, description=f'401k contribution', for_benefit_of=to)

            if _401k_match>0:

                if _401k_match>0.25*amount:
                    raise Exception(f"401k profit match {_401k_match} cannot be more than {amount*0.25}")

                self.transfer('general', account_401k, _401k_match, description=f'401k employer match', for_benefit_of=to)

        # Are we maxed out on child_care
        max_child_care = to.rates.max_child_care.loc['total'].amount
        value_child_care = sum(to.find_account(None, 'child_care')).value
        if value_child_care>0:
            max_child_care -= value_child_care

        if child_care>0:

            if child_care>max_child_care:
                raise Exception(f"child_care contribution {child_care} greater than max remaining child_care space {max_child_care}")

            account_child_care = to.find_account(self, 'child_care')
            if account_child_care is not None:
                if child_care>0:
                    to.transfer('general', account_child_care, child_care, description=f'Childcare FSA contribution', for_benefit_of=to)


    def share_profits(self, to, amount, percentage):

        pass


    def pay_dividends(self):

        pass
