import cmd
import traceback
import logging.config
from twisted.internet import reactor
import twisted.internet.error

from jtrader.broker import Broker, BrokerFactory
from jtrader.trader import Trader
from jtrader.server.database import DatabaseServer, DBServerFactory
from jtrader.server import FeedServer
from jtrader.mvc.views import ViewerFactory
from jtrader.mvc.commands import *
from jtrader.mvc.log_config import generate_log_config

from jtrader.core.common.utils import parse_file


def parse(arg):
    return arg.split()


class ControlShell(cmd.Cmd):
    intro = 'Welcome to the trading control shell.   Type help or ? to list commands.\n'
    prompt = 'JTrader: '

    def __init__(self):
        cmd.Cmd.__init__(self)
        self._broker: Broker = Broker()
        self._feed_server = FeedServer(80)

        self._viewer = ViewerFactory('console')

        self._trader = Trader()

    def configure(self, config_path):
        config = parse_file(config_path)
        logging.config.dictConfig(generate_log_config(**config['log']))

        db_config = config['database']
        db_type = db_config['db_type']
        db_server = DBServerFactory(db_type, db_config)

        strategy_manager_config = config['trader']
        self._trader.configure(strategy_manager_config)

        broker_config = config['broker']
        broker_type = broker_config['broker_type']
        broker = BrokerFactory(broker_type, broker_config)
        broker.set_db_server(db_server)
        # feed server shall first subscribe broker!!
        self._feed_server.set_subject(broker)
        self._trader.set_broker(broker)
        self._broker = broker

    def add_strategy(self, strategy):
        self._trader.add_strategy(strategy)

    def do_start(self, arg):
        """
        start system
        example: start
                 start
        """
        self._broker.start()

    def do_stop(self, arg):
        """
        stop system
        """
        self._broker.stop()
        # for id_, strategy in self._trader.strategy_dict.items():
        #     strategy.save_portfolio()

    def set_viewer(self, viewer):
        self._viewer = viewer

    def send_command(self, command_class, arg):
        command = command_class()
        command.set_viewer(self._viewer)
        try:
            command.parse(arg)
        except Exception as e:
            error_msg = traceback.format_exc()
            print("Parsing arguments failed")
            print(error_msg)
            return
        try:
            if isinstance(command, BrokerCommand):
                command.execute(self._broker)
            elif isinstance(command, TraderCommand):
                command.execute(self._trader)
            else:
                logger.info("No handling for %s", command.pretty_string())
        except Exception as e:
            error_msg = traceback.format_exc()
            print("Command execution failed")
            print(error_msg)

    def do_cancel(self, arg):
        """
        :param arg: string of order arguments, including
                   client_order_id:
                   order_type: [optional]
        example: cancel a60224c0-7f36-11e8-a9e8-d89ef32f975a
        example: cancel a60224c0-7f36-11e8-a9e8-d89ef32f975a blp
        """
        self.send_command(CancelOrderCommand, arg)

    def do_order(self, arg):
        """
        :param arg: string of order arguments, including
                   order_type: LIMIT/MARKET
                   direction: BUY/SELL
                   volume:
                   symbol:
                   price: [optional]
                   strategy_id: [optional]
                   parameter: [optional]
        example: order limit buy 0.4 BTCUSDT.BNC 6000 manual {}
        """
        self.send_command(CreateOrderCommand, arg)

    def do_status(self, arg):
        """
        :param arg: string of strategy_id, if nothing input, then output all strategies' information
        example: status MA_CROSS
        example: status
        """
        self.send_command(ShowStatusCommand, arg)

    def do_market(self, arg):
        """
        :param arg: string of strategy_id, if nothing input, then output all strategies' information
        example: market MA_CROSS
        example: market
        """
        self.send_command(ShowMarketCommand, arg)

    def do_turn(self, arg):
        """
        :param arg: string of strategy arguments, including
                   strategy_id:
                   mode: OFF/MANUAL/AUTO
        example: turn MA_CROSS MANUAL
        example: turn all OFF
        """
        self.send_command(SetModeCommand, arg)

    def do_funding(self, arg):
        """
        :param arg: string of funding arguments, including
                   strategy_id:
                   asset:
                   volume:
        example: funding MA_CROSS USDT.BNC 500
        example: funding MA_CROSS BTC.BNC -1
        """
        self.send_command(FundingCommand, arg)

    def do_query(self, arg):
        """
        :param arg:
        example: query order symbol="ETHUSD.BTX" symbol volume price direction
        """
        self.send_command(QueryCommand, arg)

    def do_algo(self, arg):
        """
        :param arg:
        :return:
        example: algo
        """
        self.send_command(ShowAlgorithmCommand, arg)

    def do_balance(self, arg):
        """
        show account balance of all APIs
        :param arg:
        :return:
        example: balance
        """
        self.send_command(ShowBalanceCommand, arg)

    def do_add_strategy(self, arg):
        """
        :param arg:
        :return:
        example: add_strategy file.json
        """
        self.send_command(AddStrategyCommand, arg)

    def do_remove_strategy(self, arg):
        """
        :param arg:
        :return:
        example: remove_strategy file.json
        """
        self.send_command(RemoveStrategyCommand, arg)

    def do_close(self, arg):
        """
        :param arg:
        :return:
        example: close ma all
                 close ma ETHUSD.BTX

        """
        self.send_command(ClosePositionCommand, arg)

    def do_clear(self, arg):
        """
        :param arg:
        :return:
        example: clear bnc USDT
        """
        self.send_command(CloseOpenPositionCommand, arg)

    def do_save_portfolio(self, arg):
        """
        :param arg:
        :return:
        example: save_portfolio ma ma.portfolio
                 save_portfolio ma

        """
        self.send_command(SavePortfolioCommand, arg)

    def do_load_portfolio(self, arg):
        """
        :param arg:
        :return:
        example: load_portfolio ma ma.portfolio
                 load_portfolio ma

        """
        self.send_command(LoadPortfolioCommand, arg)

    def do_modify_strategy(self, arg):
        """
        :param arg:
        :return:
        example: modify_strategy ma file.json
        example: modify_strategy ma
        """
        self.send_command(ModifyStrategyCommand, arg)

    def do_exec(self, arg):
        import inspect
        exec(arg)

    def do_exit(self, arg):
        """
        Exit Program
        """
        self.do_stop('')
        print('Exit Control Shell')
        try:
            reactor.stop()
        except twisted.internet.error.ReactorNotRunning:
            pass
        exit(0)
        return True

    def emptyline(self):
        return

    def onecmd(self, line):
        try:
            return cmd.Cmd.onecmd(self, line)
        except Exception as e:
            print('Error occurred when executing cmd: %s' % line)
            traceback.print_exc()


if __name__ == '__main__':
    ControlShell().cmdloop()
