class Trade(object):
    """A generic trade class.

       Defines the common attributes that all trade objects must have for
       comparison across different clearing firms and trading software"""

    def __init__(self, contract_name, quantity, price, **kwargs)
        self.contract_name = contract_name
        self.quantity = quantity
        self.price = price
        # contract_type, executing broker, conterparty, house, house, exchange, electronic, time, spread, blah blah

    def as_xml(self):
        pass
        # return Trade details as xml

    def as_dict(self):
        pass
        # return Trade details as dict

class Position(object):
    """A generic position class.

       Defines common attributes of a position object"""

    def __init__(self, contract_name, quantity, **kwargs)
        self.contract_name = contract_name
        self.quantity = quantity
