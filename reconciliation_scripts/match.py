from optionscity import OptionsCity
from newedge import NewEdgeWebsite


oc = OptionsCity(host="10.51.132.92", user="eric", passwd="ziu", db="optionscity")
OC_positions = oc.get_positions()
OC_trades = oc.get_trades()

ne = NewEdgeWebsite(userid="ERICLIU", password="Newedge1")
ne.connect()
NE_positions = ne.retrieve_positions()
NE_trades = ne.retrieve_trades()

# position matching

def total_position(instrument, positions):
    """Input a list of positions, where each position is a list [instrument_name, position]"""
    return sum([i[1] for i in filter(lambda x: x[0]==instrument, positions)])

def outer_join_positions(oc, ne):
    """Join OC and NE positions into one list.

       Inputs: lists of oc parsed positins and ne parsed positions
       format for each list is [ [instrument1, pos1],
                                 [instrument2, pos2],
                                 ...,
                                 [instrumentX, posX], ]

       Returns: list of both
       format is list of [instrument1, oc_pos, ne_pos]

       Fxn makes assumption that no instruments are repeated.
    """
    instruments = set([i[0] for i in oc] + [i[0] for i in ne])
    joined_positions = [[i,
                         total_position(i, oc),
                         total_position(i, ne)] for i in instruments]
    return joined_positions

# save these suckers for reference
OC_positions_full, NE_positions_full = OC_positions, NE_positions

joined = outer_join_positions(OC_positions, NE_positions)
position_exceptions = filter(lambda x: x[1] != x[2], joined)

# trade matching

def total_trade_and_cash(instrument, trades):
    """a trade in the trades list() looks like: [instrument_name, quantity, price]"""
    return (sum([i[1] for i in filter(lambda x: x[0]==instrument, trades)]),
            sum([i[1] * i[2] for i in filter(lambda x: x[0]==instrument, trades)])
           )

def match_exact(oc, ne, matches=[]):
    oc.sort()
    ne.sort()
    oc = list(oc)
    ne = list(ne)
    """Remove exact matching legs from lists.
       Returns 2 lists"""
    for trade in list(oc):
        if trade in ne:
            matches.append((oc.pop(oc.index(trade)), ne.pop(ne.index(trade))))
    return oc, ne, matches

def match_split_qty(oc, ne, matched_oc_split_qty=[], matched_ne_split_qty=[]):
    """Match if a strike is the same but split or priced differently.

       For example:
           -500@16 == -100@16 plus -400@16
           -200@24.5 == -100@24.4 plus -100@24.6
    """
    oc = list(oc)
    ne = list(ne)
    instruments = set([i[0] for i in oc] + [i[0] for i in ne])
    for i in instruments:
        oc_net_traded, oc_net_cash = total_trade_and_cash(i, oc)
        ne_net_traded, ne_net_cash = total_trade_and_cash(i, ne)
        if oc_net_traded == ne_net_traded and  oc_net_cash == ne_net_cash:
            # strike matches, lets take this sucker out
            matched_oc_split_qty.extend(filter(lambda x: x[0]==i, oc))
            matched_ne_split_qty.extend(filter(lambda x: x[0]==i, ne))
            oc = filter(lambda x: not x[0]==i, oc)
            ne = filter(lambda x: not x[0]==i, ne)
    return oc, ne, matched_oc_split_qty, matched_ne_split_qty

def match_spread_legs(oc, ne, matched_oc_legs=[], matched_ne_legs=[]):
    """See if cash for matching positions matches.  If so, they're spreads.
       This is a brutally inefficient process and 1 bad leg can screw it up."""

    oc = list(oc)
    ne = list(ne)
    instruments = set([i[0] for i in oc] + [i[0] for i in ne])
    potential_oc_legs = []
    potential_ne_legs = []
    for i in instruments:
        oc_net_traded, oc_net_cash = total_trade_and_cash(i, oc)
        ne_net_traded, ne_net_cash = total_trade_and_cash(i, ne)
        if oc_net_traded == ne_net_traded:
            # the quantity for a given instrument matches.
            # create a synthetic cash + position line item
            # remove individual legs from original sets
            potential_oc_legs.append([i, oc_net_traded, oc_net_cash])
            potential_ne_legs.append([i, ne_net_traded, ne_net_cash])

    # now we have all the matching legs.  see if the net prices match
    if sum([i[2] for i in potential_oc_legs]) == sum([i[2] for i in potential_ne_legs]):
        # woohoo, cash matches! These are spread legs!
        # lets take them out of the system.
        matching_instruments = [i[0] for i in potential_oc_legs]
        for i in matching_instruments:
            # add the line item to matching_legs
            matched_oc_legs.extend(filter(lambda x: x[0]==i, oc))
            matched_ne_legs.extend(filter(lambda x: x[0]==i, ne))
            # remove the line item from oc and ne
            oc = filter(lambda x: not x[0]==i, oc)
            ne = filter(lambda x: not x[0]==i, ne)
    return oc, ne, matched_oc_legs, matched_ne_legs

def are_spreads(oc, ne):
    """Determine if the contents of 2 lists are equivalent.

       Takes 2 lists of Trade objects, then determines if they are equivalent.
       If the cash matches and the quantities of each instrument are the same, it is a spread.
    """
    pass

# save these suckers for reference
OC_trades_full, NE_trades_full = OC_trades, NE_trades

OC_trades, NE_trades, exact_matches = match_exact(OC_trades, NE_trades)
OC_trades, NE_trades, OC_matched_split_qty, NE_matched_split_qty = match_split_qty(OC_trades, NE_trades)
OC_trades, NE_trades, OC_matched_legs, NE_matched_legs = match_spread_legs(OC_trades, NE_trades)

