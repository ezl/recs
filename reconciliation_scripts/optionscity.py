import MySQLdb as mysql
from datetime import date, timedelta
import re

# Regexes that I'll use to convert the OC name to the NE name

RE_instrument = re.compile(r'(?P<product>\w{1,3})'
                         r'-'
                         r'(?P<month>\D{3})'
                         r'(?P<year>\d{2})'
                         r' '
                         r'(?P<instrument>.*)')

RE_option = re.compile(r'(?P<strike>\d+)'
                       r'(?P<put_call>[PC])')

RE_future = re.compile(r'F')

# cleaning utility methods

def clean_price(px):
    return round(float(px) * 100, 2) / 100

def clean_trade_quantity(side, quantity):
    assert (side == "BID") or (side == "ASK")
    return (1 if side == "BID" else -1) * int(quantity)

def clean_instrument_name(description):
    return description

# helpers

OC_to_newedge_product_table = {"OZC": "CORN",
                               "ZC": "CORN"
                              }

def normalize_OC_instrument_to_newedge_format(ne_instrument):
    """Take an OC instrument name and convert it to New Edge format"""
    instrument = RE_instrument.match(ne_instrument)
    option = RE_option.match(instrument.group("instrument"))
    if option:
        """PUT FEB 11 CORN 580"""
        put_call = "PUT" if option.group("put_call") == "P" else "CALL"
        return "%s %s %s %s %s" % (put_call,
                                   instrument.group("month").upper(),
                                   instrument.group("year"),
                                   OC_to_newedge_product_table[instrument.group("product")],
                                   option.group("strike")
                                   )
    future = RE_future.match(instrument.group("instrument"))
    if future:
        """DEC 10 CORN"""
        return "%s %s %s" % (instrument.group("month").upper(),
                             instrument.group("year"),
                             OC_to_newedge_product_table[instrument.group("product")]
                             )
    raise Exception

# parse the raw mysql rows and convert to usable formats

def parse_trades(mysql_rows):
    return [[normalize_OC_instrument_to_newedge_format( clean_instrument_name(t[2]) ),
             clean_trade_quantity(t[0], t[1]),
             clean_price(t[3])] for t in mysql_rows]

def parse_positions(mysql_rows):
    return [[normalize_OC_instrument_to_newedge_format( clean_instrument_name(t[0]) ),
             int(t[1])] for t in mysql_rows]


class OptionsCity(object):
    def __init__(self, host, user, passwd, db):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.db = db

    def get_trades(self, commits_ago=1):
        """Get new Options City trade legs.

           commits_ago determines how many commits ago to look.  By default,
           get all trades since previous commit (1 commit ago)
        """

        # TODO: DRY -- connection component
        conn = mysql.connect(host=self.host,
                             user=self.user,
                             passwd=self.passwd,
                             db=self.db)
        cursor = conn.cursor()

        cursor.execute(self.SQL_trades % commits_ago)
        rows = cursor.fetchall()
        conn.close()
        trades = parse_trades(rows)
        return trades

    def get_positions(self):
        """Retrieve net position from Options City."""

        # TODO: DRY -- connection component
        conn = mysql.connect(host=self.host,
                             user=self.user,
                             passwd=self.passwd,
                             db=self.db)
        cursor = conn.cursor()

        cursor.execute(self.SQL_positions)
        rows = cursor.fetchall()
        conn.close()
        positions = parse_positions(rows)
        return positions

    # trades since last commit
    SQL_trades = """SELECT TRADES_SUB.side,
                             TRADES_SUB.tradedQuantity,
                             INSTRUMENTS.displaySymbol,
                             TRADES_SUB.tradedPrice
                      FROM INSTRUMENTS,
                           TRADES,
                           TRADES_SUB
                      WHERE TRADES_SUB.tradePersistId=TRADES.persistID AND
                            TRADES.tradeDateTime > %s  AND
                            INSTRUMENTS.persistID=TRADES_SUB.instrumentPersistId
                      ORDER BY TRADES_SUB.tradePersistId;
            """ % "(SELECT commitDate FROM (SELECT commitDate FROM POSITION_COMMITS ORDER BY commitDate DESC LIMIT %s) temp ORDER BY commitDate ASC LIMIT 1)"

    SQL_positions = """SELECT INSTRUMENTS.displaySymbol,
                              SUM(IF(TRADES_SUB.side="BID","1","-1") * TRADES_SUB.tradedQuantity) AS qty
                       FROM INSTRUMENTS,
                            INSTRUMENTMONTHS,
                            TRADES,
                            TRADES_SUB
                       WHERE TRADES_SUB.tradePersistId=TRADES.persistID AND
                             INSTRUMENTS.instrumentMonth=INSTRUMENTMONTHS.persistId AND
                             TRADES.tradeDateTime > "%s" AND
                             INSTRUMENTMONTHS.expiration > (SELECT commitDate FROM POSITION_COMMITS ORDER BY commitDate DESC LIMIT 1) AND
                             INSTRUMENTS.persistID=TRADES_SUB.instrumentPersistId
                       GROUP BY INSTRUMENTS.displaySymbol;
                    """ % "2000-1-1 16:00:00" # This arbitrary date is before OptionsCity existed.

if __name__ == "__main__":

    host = "10.51.132.92"
    user = "eric"
    passwd = "ziu"
    db = "optionscity"

    oc = OptionsCity(host, user, passwd, db)

    print oc.get_positions()
