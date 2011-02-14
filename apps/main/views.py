from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.generic.simple import direct_to_template
from reconciliation_scripts import match  # import (
                                          # OC_positions_full, NE_positions_full,
                                          # position_exceptions,
                                          # OC_trades_full, NE_trades_full,
                                          # exact_matches,
                                          # OC_matched_legs, NE_matched_legs,
                                          # OC_trades, NE_trades,)
from utils import cmp_instruments, summary

def homepage(request):
    return HttpResponseRedirect(reverse('trade'))

def trade(request):
    OC_trades = match.OC_trades
    NE_trades = match.NE_trades

    # trade exceptions
    unmatched_instruments = set( [t[0] for t in OC_trades] + \
                                 [t[0] for t in NE_trades]
                               )
    trade_exceptions = [ [ i,
                           filter(lambda x: x[0]==i, OC_trades),
                           filter(lambda x: x[0]==i, NE_trades),
                           summary(i, OC_trades),
                           summary(i, NE_trades)
                         ] for i in unmatched_instruments
                       ]
    trade_exceptions.sort(cmp_instruments)

    # matched legs
    matched_legs = [ [ i,
                       filter(lambda x: x[0]==i, match.OC_matched_legs),
                       filter(lambda x: x[0]==i, match.NE_matched_legs),
                           summary(i, match.OC_matched_legs),
                           summary(i, match.NE_matched_legs)
                     ] for i in set( [t[0] for t in match.OC_matched_legs] )
                   ]
    matched_legs.sort(cmp_instruments)

    # matched split quantity/price single legs
    matched_split_qty = [ [ i,
                       filter(lambda x: x[0]==i, match.OC_matched_split_qty),
                       filter(lambda x: x[0]==i, match.NE_matched_split_qty),
                           summary(i, match.OC_matched_split_qty),
                           summary(i, match.NE_matched_split_qty)
                     ] for i in set( [t[0] for t in match.OC_matched_split_qty] )
                   ]
    matched_split_qty.sort(cmp_instruments)

    # exact matches
    exact_matches = match.exact_matches

    template_name = 'trade.html'
    return direct_to_template(request, template_name, locals())

def position(request):
    print match.joined
    position_exceptions = match.position_exceptions
    [row.append(row[1] - row[2]) for row in match.position_exceptions]
    position_exceptions.sort(cmp=cmp_instruments)
    template_name = 'position.html'
    return direct_to_template(request, template_name, locals())

def helloworld(request, template='helloworld.html'):
    message = "Hello World!"
    return direct_to_template(request, template, locals())

def messages_test(request):
    messages.debug(request, 'This is a debug message.')
    messages.info(request, 'This is an info message.')
    messages.success(request, 'This is a success message.')
    messages.warning(request, 'This is a warning message.')
    messages.error(request, 'This is an error message.')
    return direct_to_template(request, 'base.html', {})

