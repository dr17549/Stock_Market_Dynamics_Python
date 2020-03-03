# -*- coding: utf-8 -*-
#
# BSE: The Bristol Stock Exchange
#
# Version 1.3; July 21st, 2018.
# Version 1.2; November 17th, 2012. 
#
# Copyright (c) 2012-2018, Dave Cliff
#
#
# ------------------------
#
# MIT Open-Source License:
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial
# portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# ------------------------
#
#
#
# BSE is a very simple simulation of automated execution traders
# operating on a very simple model of a limit order book (LOB) exchange
#
# major simplifications in this version:
#       (a) only one financial instrument being traded
#       (b) traders can only trade contracts of size 1 (will add variable quantities later)
#       (c) each trader can have max of one order per single orderbook.
#       (d) traders can replace/overwrite earlier orders, and/or can cancel
#       (d) simply processes each order in sequence and republishes LOB to all traders
#           => no issues with exchange processing latency/delays or simultaneously issued orders.
#
# NB this code has been written to be readable/intelligible, not efficient!

# could import pylab here for graphing etc

import sys
import math
import random
from BSE_Traders import populate_market, trade_stats
from BSE_Orders import Order
from BSE_Orderbook_half import Orderbook, Orderbook_half
from BSE_Exchange import Exchange
from BSE_Customer_Order import customer_orders
ticksize = 1  # minimum change in price, in cents/pennies


import csv

# one session in the market
def market_session(sess_id, starttime, endtime, trader_spec, order_schedule, dumpfile, dump_each_trade, verbose):


        # initialise the exchange
        exchange = Exchange()


        # create a bunch of traders
        traders = {}
        trader_stats = populate_market(trader_spec, traders, True, verbose)


        # timestep set so that can process all traders in one second
        # NB minimum interarrival time of customer orders may be much less than this!! 
        timestep = 1.0 / float(trader_stats['n_buyers'] + trader_stats['n_sellers'])
        # timestep = 1.0

        duration = float(endtime - starttime)

        last_update = -1.0

        time = starttime

        orders_verbose = False
        lob_verbose = False
        process_verbose = False
        respond_verbose = False
        bookkeep_verbose = False
        inside_trade_verbose = False
        mcg_names = ['MARKET_M', "LIQ", "NOISE", "MOMENTUM", "MEAN_R"]

        personal_print = []
        pending_cust_orders = []

        switch = 0
        counter_b = 0
        counter_s = len(traders) / 2

        set_d_s = False
        order_counter = 0
        time_counter = 0
        trades_num = 0
        issue_counter = 0
        if verbose: print('\n%s;  ' % (sess_id))

        while time < endtime:
                time_counter += 1
                # how much time left, as a percentage?
                time_left = (endtime - time) / duration
                trade = None

                # # this one gives assignments to traders
                [pending_cust_orders, kills], issue_new = customer_orders(time, last_update, traders, trader_stats,
                                                 order_schedule, pending_cust_orders, orders_verbose)

                if issue_new:
                    issue_counter += 1
                # customer order is assignment
                # if any newly-issued customer orders mean quotes on the LOB need to be cancelled, kill them
                if len(kills) > 0:
                        # if verbose : print('Kills: %s' % (kills))
                        for kill in kills:
                                # if verbose : print('lastquote=%s' % traders[kill].lastquote)
                                if traders[kill].lastquote != None :
                                        # if verbose : print('Killing order %s' % (str(traders[kill].lastquote)))
                                        exchange.del_order(time, traders[kill].lastquote, verbose)

                tid = list(traders.keys())[random.randint(0, len(traders) - 1)]
                # for tid in list(traders.keys()):
                # for naruto in range(0,1):
                orders_from_agent, need_to_delete_orders = traders[tid].getorder(time, time_left, exchange.publish_lob(time, lob_verbose))

                # # need to delete orders before going further
                # if len(need_to_delete_orders) > 0:
                #         for to_be_del_orders in need_to_delete_orders:
                #                 # print("BSE MAIN : DEL " + str(to_be_del_orders))
                #                 exchange.del_order(time,to_be_del_orders,process_verbose)
                #
                #
                # # if verbose: print('Trader Quote: %s' % (order))
                # if len(orders_from_agent) > 0:
                #         del_array = []
                #         del_in_exchange = []
                #         for temp_ord in range(len(traders[tid].orders)):
                #                 if (traders[tid].orders[temp_ord].qid >= 0):
                #                         del_array.append(temp_ord)
                #                         del_in_exchange.append(traders[tid].orders[temp_ord])
                #
                #         del_array.sort(reverse=True)
                #         for i in del_array:
                #                 del traders[tid].orders[i]
                #         for d_ord in del_in_exchange:
                #                 exchange.del_order(time,d_ord,True)


                if len(orders_from_agent) > 0:
                        order_counter += 1

                for order in orders_from_agent:
                        if order != None:

                                print("________ ORDER FROM AGENT ________")
                                print(str(order))
                                # if there is an order, you should first
                                # 1. delete all old records
                                #       a. delete in the personal self.orders
                                #       b. delete in the exchange lob
                                # 2. add new order -> which is done in the section below
                                #
                                # kill orders that is less than the current assignment (customer order)

                                # for temp_id in list(traders.keys()):
                                #         most_recent_order = 0
                                #
                                #         if traders[temp_id].ttype not in mcg_names:
                                #
                                #                 for iter_ord in traders[temp_id].orders:
                                #                         if iter_ord.qid < 0 and iter_ord.time > most_recent_order:
                                #                                 most_recent_order = iter_ord.time
                                #
                                #                 del_array = []
                                #                 for iter_ord in range(len(traders[temp_id].orders)):
                                #                         if traders[temp_id].orders[iter_ord].time < most_recent_order:
                                #                                 del_array.append(iter_ord)
                                #
                                #                 del_array.sort(reverse=True)
                                #                 for i in del_array:
                                #                         del traders[temp_id].orders[i]
                                #
                                #         else:
                                #                 for iter_ord in traders[temp_id].orders:
                                #                         if iter_ord.qid < 0 and iter_ord.time > most_recent_order:
                                #                                 most_recent_order = iter_ord.time
                                #
                                #                 del_array = []
                                #                 for iter_ord in range(len(traders[temp_id].orders)):
                                #                         if traders[temp_id].orders[iter_ord].time < most_recent_order \
                                #                                 and traders[temp_id].orders[iter_ord].qid < 0:
                                #                                         del_array.append(iter_ord)
                                #                 del_array.sort(reverse=True)
                                #                 for i in del_array:
                                #                         del traders[temp_id].orders[i]
                                #
                                #
                                # # check for orders inside the agent object
                                # # __________________________________________________________________________
                                # two_order_traders = ['MARKET_M', 'GVWY', 'SNPR', 'ZIC', "SHVR", "ZIP"]
                                # no_order_traders = ['LIQ', 'MOMENTUM']
                                # for temp_id in list(traders.keys()):
                                #         if traders[temp_id].ttype in two_order_traders:
                                #                 if len(traders[temp_id].orders) > 2:
                                #                         print("TYPE : " + str(traders[
                                #                                                       temp_id].ttype) + " ORDER N : " + str(
                                #                                 len(traders[temp_id].orders)))
                                #                         for temp_ord in traders[temp_id].orders:
                                #                                 print(temp_ord)
                                #                         sys.exit(
                                #                                 "Trader orders not equal as required amount ")
                                #         elif traders[temp_id].ttype in no_order_traders:
                                #                 if len(traders[temp_id].orders) > 1:
                                #                         print("TYPE : " + str(traders[
                                #                                                       temp_id].ttype) + " ORDER N : " + str(
                                #                                 len(traders[temp_id].orders)))
                                #                         for temp_ord in traders[temp_id].orders:
                                #                                 print(temp_ord)
                                #                         sys.exit(
                                #                                 "Trader orders not equal as required amount ")
                                #         else:
                                #                 if len(traders[temp_id].orders) > 1:
                                #                         print("TYPE : " + str(traders[
                                #                                                       temp_id].ttype) + " ORDER N : " + str(
                                #                                 len(traders[temp_id].orders)))
                                #                         for temp_ord in traders[temp_id].orders:
                                #                                 print(temp_ord)
                                #                         sys.exit(
                                #                                 "Trader orders not equal as required amount ")
                                # # __________________________________________________________________________


                                # now we kill the orders that is less than the current one
                                # send order to exchange
                                if order.qty < 1:
                                        sys.exit("Order Quantity cannot be 0")
                                traders[tid].n_quotes = 1

                                # if inside_trade_verbose:
                                #         print("^^^^^^ ORDER FROM AGENT " + str(order))
                                #
                                # for trader_id in list(traders.keys()):
                                #         qid = []
                                #         for a_ord in traders[trader_id].orders:
                                #                 if a_ord.qid not in qid:
                                #                         qid.append(a_ord.qid)
                                #                 else:
                                #                         print("TRADER TYPE : " + str(traders[trader_id].ttype))
                                #                         for p_order in traders[trader_id].orders:
                                #                                 print(p_order)
                                #                         sys.exit("Double QID in the same list")

                                transac_record, actual_quantity_traded = exchange.process_order2(time, order, process_verbose,list(traders.keys()), traders)


                                if len(transac_record) != 0:
                                        traders[tid].add_order(order, False)

                                        for trade in transac_record:
                                                trades_num += 1

                                                # if traders[trade['party1']].ttype == 'MEAN_R' or traders[trade['party2']].ttype == 'MEAN_R':
                                                #         personal_print.append([time, trade['price']])
                                                #
                                                # if inside_trade_verbose:
                                                #         print("^^^^^^ ORDER TRADED BETWEEN SUBMITTED : " + str(tid) + " CLIENT : " + str(trade['party2']) +
                                                #               " PRICE : " + str(trade['price']) + " Original QTY : " + str(order.qty))
                                                #
                                                # if verbose:
                                                #         print("___ BEFORE BOOK KEEP : TRADE FROM AGENTS ____ ")
                                                #         for indv_o in traders[trade['party1']].orders:
                                                #                 print(str(trade['party1']) + " : " + str(indv_o))
                                                #         print(" ------------------------------------------------")
                                                #         for indv_o in traders[trade['party2']].orders:
                                                #                 print(str(trade['party2']) + " : " + str(indv_o))
                                                #         print("_____________________________________________ ")

                                                # if verbose:
                                                #         print("TRADE TID " + str(trade['party2']) + " DEL ORD ? : " + str(trade['del_party2']) )
                                                #         print("TRADE TID " + str(trade['party1']) + " DEL ORD ? : " + str(
                                                #         trade['del_party1']))
                                                traders[trade['party1']].bookkeep(trade, order, bookkeep_verbose, time, actual_quantity_traded,trade['del_party1'])
                                                traders[trade['party2']].bookkeep(trade, order, bookkeep_verbose, time, actual_quantity_traded,trade['del_party2'])

                                                # if verbose:
                                                #         print("___ AFTER BOOK KEEP : TRADE FROM AGENTS ____ ")
                                                #         for indv_o in traders[trade['party1']].orders:
                                                #                 print(str(trade['party1']) + " : " + str(indv_o))
                                                #         print(" ------------------------------------------------")
                                                #         for indv_o in traders[trade['party2']].orders:
                                                #                 print(str(trade['party2']) + " : " + str(indv_o))
                                                #         print("_____________________________________________ ")
                                                if dump_each_trade: trade_stats(sess_id, traders, tdump, time, exchange.publish_lob(time, lob_verbose))

                                                # check if the MKT order is still in the agent personal order, if yes, must be removed
                                                # if order.ostyle == 'MKT':
                                                #         for temp_ord in traders[tid].orders:
                                                #                 if temp_ord.qid == order.qid:
                                                #                         traders[tid].orders.remove(temp_ord)


                                # if there is no trade
                                # else:
                                #         if order.ostyle == 'LIM':
                                #                 traders[tid].add_order(order, False)

                                # traders respond to whatever happened
                                lob = exchange.publish_lob(time, lob_verbose)

                                for t in traders:
                                        # NB respond just updates trader's internal variables
                                        # doesn't alter the LOB, so processing each trader in
                                        # sequence (rather than random/shuffle) isn't a problem
                                        traders[t].respond(time, lob, trade, respond_verbose)

                # check if the exchange matches the trader personal orders
                # __________________________________________________________________________
                # check both lob and orders in the exchange
                # orderlist.append([order.time, order.qty, order.tid, order.qid])

                # for price in exchange.bids.lob:
                #
                #         for order in exchange.bids.lob[price][1]:
                #                 found = False
                #
                #                 for personal_order in traders[order[2]].orders:
                #                         if personal_order.qty == order[1] and price == personal_order.price and order[0] == personal_order.time:
                #                                 found = True
                #                 if not found:
                #                         print("ORDER IN LOB : NOT FOUND TID  : " + str(order) + " - TYPE :" + str(traders[order[2]].ttype))
                #                         print(exchange.bids.lob[price])
                #                         print("_______________________")
                #                         for p_order in traders[order[2]].orders:
                #                                 print(p_order)
                #                         sys.exit("Order in the trader and order in the LOB does not match")
                #
                #
                # for price in exchange.asks.lob:
                #         for order in exchange.asks.lob[price][1]:
                #                 found = False
                #
                #                 for personal_order in traders[order[2]].orders:
                #                         if personal_order.qty == order[1] and price == personal_order.price and order[0] == personal_order.time:
                #                                 found = True
                #                 if not found:
                #                         print("ORD IN LOB : NOT FOUND TID  : " + str(order) + str(traders[order[2]].ttype))
                #                         print(exchange.asks.lob[price])
                #                         print("_______________________")
                #                         for p_order in traders[order[2]].orders:
                #                                 print(p_order)
                #                         sys.exit("Order in the trader and order in the LOB does not match")
                # # __________________________________________________________________________
                #
                # for temp_id in list(traders.keys()):
                #         for temp_ord in traders[temp_id].orders:
                #                 if temp_ord.qid > 0 and traders[temp_id].ttype in mcg_names:
                #                         found = False
                #                         if temp_ord.otype == 'Bid':
                #                                 ord_check_book = exchange.bids.lob
                #                         else:
                #                                 ord_check_book = exchange.asks.lob
                #
                #                         if temp_ord.price not in ord_check_book:
                #                                 print("TEMPORD : " + str(temp_ord))
                #                                 print("LOB : " + str(ord_check_book))
                #                                 sys.exit("PRICE is not in the lob")
                #                         for list_info in ord_check_book[temp_ord.price][1]:
                #                                 # [order.time, order.qty, order.tid, order.qid]
                #                                 if list_info[1] == temp_ord.qty and list_info[2] == temp_id and list_info[3] == temp_ord.qid:
                #                                         found = True
                #
                #                         if not found:
                #                                 print("_______________________")
                #                                 print("ORDER NOT FOUND for TRADER : TID - " + str(temp_id) + " TYPE :" + str(traders[temp_id].ttype))
                #                                 print("LOB : " + str(ord_check_book))
                #                                 print("ORDER NOT FOUND : " + str(temp_ord))
                #                                 sys.exit("Order in trader does not match LOB")

                if exchange.asks.best_price is not None and exchange.bids.best_price is not None:
                        if time % 10 == 0:
                                mid_price = ( exchange.bids.best_price + exchange.asks.best_price) / 2
                                personal_print.append([time, mid_price])



                time = time + timestep

        print("END OF TRANSACTION DAY")
        print("Total Orders : " + str(order_counter))
        print("Time Counter : " + str(time_counter))
        print("Trades Num : " + str(trades_num))
        print("Issue Counter : " + str(issue_counter))

        # end of an experiment -- dump the tape
        exchange.tape_dump('transaction.csv', 'w', 'keep')
        print_trader_type_transac(personal_print)


        # write trade_stats for this experiment NB end-of-session summary only
        trade_stats(sess_id, traders, tdump, time, exchange.publish_lob(time, lob_verbose))


def print_trader_type_transac(row_list):
        with open('mid_price.csv', 'w') as file:
                writer = csv.writer(file)
                writer.writerows(row_list)

#############################

# # Below here is where we set up and run a series of experiments


if __name__ == "__main__":

        # set up parameters for the session

        start_time = 0.0
        end_time = 300.0
        duration = end_time - start_time


        # schedule_offsetfn returns time-dependent offset on schedule prices
        def schedule_offsetfn(t):
                pi2 = math.pi * 2
                c = math.pi * 3000
                wavelength = t / c
                gradient = 100 * t / (c / pi2)
                amplitude = 100 * t / (c / pi2)
                offset = gradient + amplitude * math.sin(wavelength * t)
                return int(round(offset, 0))
                
                

# #        range1 = (10, 190, schedule_offsetfn)
# #        range2 = (200,300, schedule_offsetfn)

# #        supply_schedule = [ {'from':start_time, 'to':duration/3, 'ranges':[range1], 'stepmode':'fixed'},
# #                            {'from':duration/3, 'to':2*duration/3, 'ranges':[range2], 'stepmode':'fixed'},
# #                            {'from':2*duration/3, 'to':end_time, 'ranges':[range1], 'stepmode':'fixed'}
# #                          ]



        supply_schedule = [ {'from':start_time, 'to':end_time, 'ranges':[(50,500)], 'stepmode':'fixed'}
                          ]

        demand_schedule = [ {'from':start_time, 'to':end_time, 'ranges':[(50,500)], 'stepmode':'fixed'}
                          ]

        order_sched = {'sup':supply_schedule, 'dem':demand_schedule,
                       'interval':30, 'timemode':'periodic'}

        # run a sequence of trials that exhaustively varies the ratio of four trader types
        # NB this has weakness of symmetric proportions on buyers/sellers -- combinatorics of varying that are quite nasty
        


        fname = 'balances_'

        tdump = open(fname, 'w')

        min_n = 1

        trialnumber = 1
        buyers_spec = [('LIQ', 0), ('GVWY', 0),
                                                       ('ZIP', 10), ('MOMENTUM', 0), ('MARKET_M', 0),('MEAN_R', 0),('NOISE', 0)]
        sellers_spec = buyers_spec
        traders_spec = {'sellers':sellers_spec, 'buyers':buyers_spec}


        trial_id = 'trial%07d' % trialnumber
        market_session(trial_id, start_time, end_time, traders_spec,
                       order_sched, tdump, False, False)
        tdump.flush()
        


