# helper function

def cmp_instruments(x, y):
    """Order instruments for display.

    In [31]: baz.split()
    Out[32]: ['PUT', 'DEC', '10', 'CORN', '500']

    In [33]: foo.split()
    Out[33]: ['DEC', '10', 'CORN']
    """
    x_tokens = x[0].split()
    y_tokens = y[0].split()
    # futures are "smaller" (we want them at the top of the list)
    if len(x_tokens) != (y_tokens):
        return cmp(len(x_tokens), len(y_tokens))

    if x_tokens[0] == "PUT" or x_tokens[0] == "CALL":
        # if option: compare options by expiration, then strike, then put/call
        if x_tokens[2] != y_tokens[2]:
            # year
            return cmp(x_tokens[2], y_tokens[2])
        elif x_tokens[1] != y_tokens[1]:
            # month
            return cmp(x_tokens[1], y_tokens[1])
        elif x_tokens[4] != y_tokens[4]:
            # strike
            return cmp(x_tokens[4], y_tokens[4])
        else:
            # put/call
            return cmp(x_tokens[0], y_tokens[0])
    else:
        # its a fut, compare by exp
        if x_tokens[1] != y_tokens[1]:
            # year
            return cmp(x_tokens[1], y_tokens[1])
        elif x_tokens[0] != y_tokens[0]:
            # month
            return cmp(x_tokens[0], y_tokens[0])

def summary(instrument, trades):
    """takes a trades list item as an input,
       formatted as [instrument_name, qty, price] and
       returns [bought qty, bought average px, sold qty, sold avg price]"""
    buys = filter(lambda x: x[0]==instrument and x[1] > 0, trades)
    sales = filter(lambda x: x[0]==instrument and not x[1] > 0, trades)
    total_bought = sum([i[1] for i in buys])
    try:
        average_buy_price = sum([i[1] * i[2] for i in buys]) / total_bought
    except ZeroDivisionError:
        average_buy_price = sum([i[1] * i[2] for i in buys])
    total_sold = sum([i[1] for i in sales])
    try:
        average_sale_price = sum([i[1] * i[2] for i in sales]) / total_sold
    except ZeroDivisionError:
        average_sale_price = sum([i[1] * i[2] for i in sales])
    return (total_bought, average_buy_price, total_sold, average_sale_price)

