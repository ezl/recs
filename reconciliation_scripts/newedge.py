import urllib
import urllib2
from lxml import etree
import re

# I can't extract only the columns I want when pulling the CSV, so I use transpose twice to filter it out

def transpose(x):
    return zip(*x)

def separate_headers(csv):
    csv = csv.replace('"','')
    data = [row.strip().split(",") for row in csv.strip().split("\n")]
    headers = data[0]
    rows = data [1:]
    return headers, rows

# cleaning utility methods

def clean_price(px):
    return round(float(px) * 10000, 4) / 100

def clean_trade_quantity(buy_sell_code, abs_qty):
    """Both inputs are strings from New edge.

       New edge codes: for buy=1, sell=2
       Quantity comes as a string, convert it to int
    """
    assert (buy_sell_code == "B") or (buy_sell_code == "S")
    return (1 if buy_sell_code =="B" else -1) * int(float(abs_qty))

def clean_instrument_name(description):
    return re.sub("\s{2,}"," ", description)

# parse the csv and put them into lists to match the OC lists

def parse_trades(csv):
    headers, rows = separate_headers(csv)
    relevant_columns = ["B/S", "Quantity", "Contract Description", "Trade_price"]
    relevant_column_indices = map(lambda x: headers.index(x), relevant_columns)
    filtered = transpose([transpose(rows)[i] for i in relevant_column_indices])
    return [[clean_instrument_name(t[2]),
             clean_trade_quantity(t[0], t[1]),
             clean_price(t[3])]
            for t in filtered]

def parse_positions(csv):
    headers, rows = separate_headers(csv)
    relevant_columns = ["Contract Description", "Net Qty"]
    relevant_column_indices = map(lambda x: headers.index(x), relevant_columns)
    filtered = transpose([transpose(rows)[i] for i in relevant_column_indices])
    return [[clean_instrument_name(t[0]), int(t[1])] for t in filtered]


class NewEdgeWebsite(object):
    def __init__(self, userid="ERICLIU", password="Ctc12345"):
        self.userid = userid
        self.password = password

        # build opener with HTTPCookieProcessor
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        urllib2.install_opener(self.opener)

        self.credentials = urllib.urlencode(dict(userid=self.userid, password=self.password))

    def _curl(self, url, method="GET", referer=None):
        if referer is None:
            referer = "http://python.org"
        user_agent = "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.517.41 Safari/534.7"
        self.request_headers = {"User-Agent": user_agent, "Referer": referer}
        request = urllib2.Request(url, headers=self.request_headers)
        if method == "GET":
            f = self.opener.open(request)
        else: # method == "POST"
            f = self.opener.open(request, self.credentials)

        page = f.read()
        f.close()
        return page

    def connect(self):
        """Not sure why, but newedge seems to complain if I don't hit the main page and the report landing page"""

        print "Logging in to DataPort..."
        url = "https://pulse.newedgegroup.com/wps/myportal"
        self._curl(url, method="POST")

        #WTF? I have no idea why i need to hit this page
        print "Accessing report landing page..."
        url = "https://pulsedataport.newedgegroup.com/wps/myportal/reports"
        self._curl(url)

    def retrieve_trades(self):
        print "Retrieving real time trades..."
        url = "https://pulsedataport.newedgegroup.com/wps/PA_dataport-report-na/crystalExport.jsp?exportFormat=CSV&repid=31934186&archid=31934561"
        page = self._curl(url, method="GET")
        trades = parse_trades(page)
        return trades

    def retrieve_positions(self):
        print "Retrieving open position..."
        url = "https://pulsedataport.newedgegroup.com/wps/PA_dataport-report-na/crystalExport.jsp?exportFormat=CSV&repid=31934370&archid=33260099"
        page = self._curl(url, method="GET")
        positions = parse_positions(page)
        return positions
