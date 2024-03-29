import sys
import collections
from BSE_Customer_Order import bse_sys_maxprice, bse_sys_minprice


# Orderbook_half is one side of the book: a list of bids or a list of asks, each sorted best-first
class Orderbook_half:

        def __init__(self, booktype, worstprice):
                # booktype: bids or asks?
                self.booktype = booktype
                # dictionary of orders received, indexed by Trader ID
                self.orders = {}
                # limit order book, dictionary indexed by price, with order info
                self.lob = {}
                # anonymized LOB, lists, with only price/qty info
                self.lob_anon = []
                # summary stats
                self.best_price = None
                self.best_tid = None
                self.best_qty = 0
                self.worstprice = worstprice
                self.n_orders = 0  # how many orders?
                self.lob_depth = 0  # how many different prices on lob?


        def anonymize_lob(self):
                # anonymize a lob, strip out order details, format as a sorted list
                # NB for asks, the sorting should be reversed
                self.lob_anon = []
                for price in sorted(self.lob):
                        qty = self.lob[price][0]
                        self.lob_anon.append([price, qty])


        def build_lob(self):
                lob_verbose = False
                # take a list of orders and build a limit-order-book (lob) from it
                # NB the exchange needs to know arrival times and trader-id associated with each order
                # returns lob as a dictionary (i.e., unsorted)
                # also builds anonymized version (just price/quantity, sorted, as a list) for publishing to traders
                self.lob = {}
                for tid in self.orders:
                        order = self.orders.get(tid)
                        price = order.price
                        if price in self.lob:
                                # update existing entry
                                qty = self.lob[price][0]
                                orderlist = self.lob[price][1]
                                orderlist.append([order.time, order.qty, order.tid, order.qid])
                                self.lob[price] = [qty + order.qty, orderlist]
                        else:
                                # create a new dictionary entry
                                self.lob[price] = [order.qty, [[order.time, order.qty, order.tid, order.qid]]]
                # create anonymized version
                self.lob = collections.OrderedDict(sorted(self.lob.items(), reverse=True))
                self.anonymize_lob()
                # record best price and associated trader-id
                if len(self.lob) > 0 :
                        if self.booktype == 'Bid':
                                self.best_price = self.lob_anon[-1][0]
                                self.best_qty = self.lob_anon[-1][1]
                        else :
                                self.best_price = self.lob_anon[0][0]
                                self.best_qty = self.lob_anon[0][1]
                        self.best_tid = self.lob[self.best_price][1][0][2]
                else :
                        self.best_price = None
                        self.best_tid = None
                        self.best_qty = 0

                if lob_verbose : print(self.lob)


        def book_add(self, order):
                # add order to the dictionary holding the list of orders
                # either overwrites old order from this trader
                # or dynamically creates new entry in the dictionary
                # so, max of one order per trader per list
                # checks whether length or order list has changed, to distinguish addition/overwrite
                #print('book_add > %s %s' % (order, self.orders))
                n_orders = self.n_orders
                self.orders[order.tid] = order
                self.n_orders = len(self.orders)
                self.build_lob()

                # print(self.n_orders)
                # print("ADDED LOB" + str(self.lob))

                #print('book_add < %s %s' % (order, self.orders))
                if n_orders != self.n_orders :
                    return('Addition')
                else:
                    return('Overwrite')



        def book_del(self, order):
                # delete order from the dictionary holding the orders
                # assumes max of one order per trader per list
                # checks that the Trader ID does actually exist in the dict before deletion
                # print('book_del %s',self.orders)
                if self.orders.get(order.tid) != None :
                        del(self.orders[order.tid])
                        self.n_orders = len(self.orders)
                        self.build_lob()
                # print('book_del %s', self.orders)

        def delete_best(self, oppo_tid, remaining_qty):
                verbose = False
                del_in_trader = False
                quantity_decremented = 1
                if verbose:
                        print("BEFORE LOB :" + str(self.lob))
                # delete order: when the best bid/ask has been hit, delete it from the book
                # the TraderID of the deleted order is return-value, as counterparty to the trade
                best_price_orders = self.lob[self.best_price]
                trade_price = self.best_price
                best_price_qty = best_price_orders[0]
                best_price_counterparty = best_price_orders[1][0][2]
                order_del_qid = best_price_orders[1][0][3]
                if oppo_tid == best_price_counterparty:
                        # best_price_orders = self.lob[1]
                        if self.booktype == 'Bid':
                                second_best_price = list(self.lob)[1]

                        else:
                                second_best_price = list(self.lob)[len(self.lob) - 2]
                        print("Second best price : " + str(second_best_price))
                        trade_price = second_best_price
                        best_price_orders  = self.lob[second_best_price]
                        best_price_qty = best_price_orders[0]
                        best_price_counterparty = best_price_orders[1][0][2]
                        order_del_qid = best_price_orders[1][0][3]

                        if best_price_qty == 1:
                                del_in_trader = True
                                del (self.lob[second_best_price])
                                del (self.orders[best_price_counterparty])
                                self.n_orders = self.n_orders - 1
                                quantity_decremented = 1
                        else:
                                if best_price_qty < remaining_qty:
                                        quantity_decremented = best_price_qty
                                else:
                                        quantity_decremented = remaining_qty

                                lob_list = best_price_orders[1]
                                first_order_quantity = best_price_orders[1][0][1]
                                self.best_qty -= 1
                                # must delete if the order quantity is the same
                                if first_order_quantity > quantity_decremented:
                                        lob_list[0][1] = first_order_quantity - quantity_decremented
                                        self.lob[second_best_price] = [best_price_qty - quantity_decremented, lob_list]
                                else:
                                        self.n_orders -= 1
                                        self.lob[second_best_price] = [best_price_qty - quantity_decremented, best_price_orders[1][:1]]

                                if first_order_quantity > quantity_decremented:
                                        # it's the pointer pointing to the same order, so this also decreases the quantity in the trader
                                        change_qty = self.orders[best_price_counterparty].qty
                                        self.orders[best_price_counterparty].qty = change_qty - quantity_decremented

                                else:
                                        del_in_trader = True
                                        del (self.orders[best_price_counterparty])

                elif best_price_qty == 1:
                        trade_price = self.best_price
                        del_in_trader = True

                        del(self.lob[self.best_price])
                        del(self.orders[best_price_counterparty])
                        quantity_decremented = 1
                        del_in_trader = True
                        self.n_orders = self.n_orders - 1
                        if self.n_orders > 0:
                                if self.booktype == 'Bid':
                                        self.best_price = max(self.lob.keys())
                                else:
                                        self.best_price = min(self.lob.keys())
                                self.best_qty = self.lob[self.best_price][0]
                                self.lob_depth = len(self.lob.keys())
                        else:
                                self.best_price = self.worstprice
                                self.lob_depth = 0
                                self.best_qty = 0
                elif best_price_qty > 1:
                        trade_price = self.best_price
                        if best_price_qty < remaining_qty:
                                quantity_decremented = best_price_qty
                        else:
                                quantity_decremented = remaining_qty


                        lob_list = best_price_orders[1]
                        first_order_quantity = best_price_orders[1][0][1]
                        self.best_qty -= quantity_decremented

                        # correct - delete chunk
                        if first_order_quantity > quantity_decremented:
                                lob_list[0][1] = first_order_quantity - 1
                                self.lob[self.best_price] = [best_price_qty - quantity_decremented, lob_list]
                        else:
                                self.n_orders -= 1
                                self.lob[self.best_price] = [best_price_qty - quantity_decremented, best_price_orders[1][:1]]

                        if first_order_quantity > quantity_decremented:
                                # it's the pointer pointing to the same order, so this also decreases the quantity in the trader
                                change_qty = self.orders[best_price_counterparty].qty
                                self.orders[best_price_counterparty].qty = change_qty - quantity_decremented

                        else:
                                del_in_trader = True
                                del (self.orders[best_price_counterparty])

                else:
                        print("No order at the other side of the BOOK.")

                self.build_lob()
                return best_price_counterparty, order_del_qid, del_in_trader, trade_price, quantity_decremented

        def delete_best_old(self):
                # delete order: when the best bid/ask has been hit, delete it from the book
                # the TraderID of the deleted order is return-value, as counterparty to the trade
                best_price_orders = self.lob[self.best_price]
                best_price_qty = best_price_orders[0]
                best_price_counterparty = best_price_orders[1][0][2]
                if best_price_qty == 1:
                        # here the order deletes the best price
                        del (self.lob[self.best_price])
                        del (self.orders[best_price_counterparty])
                        self.n_orders = self.n_orders - 1
                        if self.n_orders > 0:
                                if self.booktype == 'Bid':
                                        self.best_price = max(self.lob.keys())
                                else:
                                        self.best_price = min(self.lob.keys())
                                self.lob_depth = len(self.lob.keys())
                        else:
                                self.best_price = self.worstprice
                                self.lob_depth = 0
                else:
                        # best_bid_qty>1 so the order decrements the quantity of the best bid
                        # update the lob with the decremented order data
                        self.lob[self.best_price] = [best_price_qty - 1, best_price_orders[1][1:]]

                        # update the bid list: counterparty's bid has been deleted
                        del (self.orders[best_price_counterparty])
                        self.n_orders = self.n_orders - 1
                self.build_lob()
                return best_price_counterparty


        def decrement_order(self,price,tid, quantity_decremented):
                verbose = False
                del_in_trader = False
                if verbose:
                        print("DEC ORDER _ BEFORE LOB :" + str(self.lob))

                # check to avoid deleting NULL entries
                if(self.lob[price] == None):
                        sys.exit("Trying to delete unknown price in the LOB")

                found_tid = False
                for entries in self.lob[price][1]:
                        if entries[2] == tid:
                                found_tid = True

                if not found_tid:
                        sys.exit("Trying to match to trader with unknown order")

                # LOB ENTRIES
                # --------------------------
                # update existing entry
                # qty = self.lob[price][0]
                # orderlist = self.lob[price][1]
                # orderlist.append([order.time, order.qty, order.tid, order.qid])

                # delete order: when the best bid/ask has been hit, delete it from the book
                # the TraderID of the deleted order is return-value, as counterparty to the trade
                best_price_orders = self.lob[price]
                best_price_qty = best_price_orders[0]
                best_price_counterparty = tid


                if best_price_qty == 1:
                        '''' This is the case where the quantity at that price is 1 as well as the number of
                        orders, so we just delete that price '''
                        del_in_trader = True
                        del (self.lob[self.best_price])
                        del (self.orders[best_price_counterparty])
                        self.n_orders = self.n_orders - 1
                        if self.n_orders > 0:
                                if self.booktype == 'Bid':
                                        self.best_price = max(self.lob.keys())
                                else:
                                        self.best_price = min(self.lob.keys())
                                self.best_qty = self.lob[self.best_price][0]
                                self.lob_depth = len(self.lob.keys())
                        else:
                                self.best_price = self.worstprice
                                self.lob_depth = 0
                elif best_price_qty > 1:
                        ''' todo Now we consider two more complicated cases:
                         FIRST OF ALL : Check if in that list, the TID is correct
                         Then 1. check if there is only 1 element in that price level, if yes, then decrease both the quantity inside and the quantity overall
                               2. IF NOT then decremenet the right order from the right trader, then decremenet the overall quantity as well '''

                        # decrease quantity in the right element
                        first_order_quantity = self.lob[price][0]
                        trade_quantity_before_dec = 0
                        for agent_submitted in range(len(self.lob[price][1])):
                                if self.lob[price][1][agent_submitted][2] == best_price_counterparty:
                                        trade_quantity_before_dec = self.lob[price][1][agent_submitted][1]
                                        if self.lob[price][1][agent_submitted][1] == quantity_decremented:
                                                self.lob[price][1].remove(self.lob[price][1][agent_submitted])
                                                # del(self.lob[price][1][agent_submitted])
                                                self.n_orders -= 1
                                                break
                                        else:
                                                # first_order_quantity = self.lob[price][1][agent_submitted][1]
                                                self.lob[price][1][agent_submitted][1] -= quantity_decremented
                                                break

                                        # element_in_lobprice = agent_submitted

                        #decrement quantity overall
                        self.lob[price][0] -= 1
                        self.best_qty -= quantity_decremented


                        if trade_quantity_before_dec > quantity_decremented:
                                # self.orders[best_price_counterparty].qty -= 1
                                change_qty = self.orders[best_price_counterparty].qty
                                self.orders[best_price_counterparty].qty = change_qty - quantity_decremented

                        else:
                                del_in_trader = True
                                del(self.orders[best_price_counterparty])


                else:
                        sys.exit("DEC ORDER cannot find the specified order in the LOB ")

                self.build_lob()

                if verbose:
                        print("DEC ORDER _ AFTER LOB :" + str(self.lob))
                return del_in_trader

# Orderbook for a single instrument: list of bids and list of asks

class Orderbook(Orderbook_half):

        def __init__(self):
                self.bids = Orderbook_half('Bid', bse_sys_minprice)
                self.asks = Orderbook_half('Ask', bse_sys_maxprice)
                self.tape = []
                self.quote_id = 0  #unique ID code for each quote accepted onto the book

