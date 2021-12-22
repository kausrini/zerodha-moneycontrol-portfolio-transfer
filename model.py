class ZerodhaContractNote:
    def __init__(self, contract_dict):
        self.contract_note_no = contract_dict['id']
        self.trade_date = contract_dict['timestamp']
        # Following contains list of transactions in a contract note
        self.trades = self.parse_trades(contract_dict['trades']['trade'])

        charges = contract_dict['totals']['grandtotals']['grandtotal']
        self.non_brokerage_charges = 0.0

        for charge in charges:
            if charge['name'] == 'Stamp Duty':
                self.stamp_duty = float(charge['value'])
                self.non_brokerage_charges += self.stamp_duty
            elif charge['name'] == 'Exchange Transaction Charges':
                self.exchange_transaction_charges = float(charge['value'])
                self.non_brokerage_charges += self.exchange_transaction_charges
            elif charge['name'] == 'Central GST':
                self.central_gst = float(charge['value'])
                self.non_brokerage_charges += self.central_gst
            elif charge['name'] == 'Securities Transaction Tax':
                self.securities_transaction_tax = float(charge['value'])
                self.non_brokerage_charges += self.securities_transaction_tax
            elif charge['name'] == 'SEBI Turnover Fees':
                self.sebi_turnover_fees = float(charge['value'])
                self.non_brokerage_charges += self.sebi_turnover_fees
            elif charge['name'] == 'Clearing Charges':
                self.clearing_charges = float(charge['value'])
                self.non_brokerage_charges += self.clearing_charges
            elif charge['name'] == 'Brokerage':
                self.brokerage = float(charge['value'])
            elif charge['name'] == 'Integrated GST':
                self.integrated_gst = float(charge['value'])
                self.non_brokerage_charges += self.integrated_gst
            elif charge['name'] == 'State GST':
                self.state_gst = float(charge['value'])
                self.non_brokerage_charges += self.state_gst
            elif charge['name'] == 'Exchange Obligation Account':
                # This is the total amount of securities purchased or sold
                self.exchange_obligation_amount = float(charge['value'])

        self.total_charges = self.brokerage + self.non_brokerage_charges

        for trade in self.trades:
            trade.trade_percentage_of_contract = trade.net_total/float(self.exchange_obligation_amount)

    @staticmethod
    def parse_trades(trades_data):
        trades = []
        if type(trades_data) is dict:
            trades_data = [trades_data]

        for trade_data in trades_data:
            trades.append(Trade(trade_data))

        return trades


class Trade:
    def __init__(self, trade_data_dict):
        self.exchange = trade_data_dict['exchange']
        self.order_no = trade_data_dict['order_id']
        self.order_time = None
        self.trade_no = trade_data_dict['id']
        self.trade_time = trade_data_dict['timestamp']
        self.security_ticker = trade_data_dict['@instrument_id'].split(':')[1]
        self.transaction_type = trade_data_dict['type']
        self.quantity = trade_data_dict['quantity']
        # Trade Price Per Unit
        self.gross_rate = float(trade_data_dict['average_price'])
        # self.transaction_brokerage = None
        # self.net_rate = None
        # self.closing_rate = None
        self.net_total = float(trade_data_dict['value'])
        # self.remarks = None
        self.isin = None
        # Percentage of trade with respect to total trade on the contract note
        self.trade_percentage_of_contract = 0.0


